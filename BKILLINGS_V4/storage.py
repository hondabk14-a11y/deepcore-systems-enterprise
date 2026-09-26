"""Durable event ledger and persistent single-vote locks for a fixed committee."""
import json
import os
import sqlite3
from pathlib import Path
from protocol import (canonical, digest, genesis, initial_state, spec_id, validate_spec,
                      validate_proposal, verify_certificate, public, vote_message, integer, hexvalue)


class Ledger:
    def __init__(self, path, spec, create=False, checkpoint=None):
        validate_spec(spec)
        self.spec = json.loads(canonical(spec))
        self.checkpoint = checkpoint
        path = Path(path)
        if not path.exists() and not create: raise ValueError('Database missing; explicit initialization required')
        if create:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        self.db = sqlite3.connect(path.resolve().as_uri()+'?mode=rw', uri=True, isolation_level=None, timeout=10)
        try:
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            if create:
                self.db.execute('BEGIN IMMEDIATE')
                self.db.execute('CREATE TABLE meta (id INTEGER PRIMARY KEY CHECK(id=1), spec TEXT NOT NULL, height INTEGER NOT NULL, head TEXT NOT NULL)')
                self.db.execute('CREATE TABLE blocks (height INTEGER PRIMARY KEY, body TEXT NOT NULL, certificate TEXT NOT NULL)')
                self.db.execute('CREATE TABLE locks (validator TEXT NOT NULL, height INTEGER NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(validator,height))')
                self.db.execute('INSERT INTO meta VALUES(1,?,?,?)', (spec_id(spec), 0, genesis(spec)))
                self.db.commit()
            self.snapshot()
        except BaseException:
            self.db.rollback(); self.db.close()
            raise

    def _replay(self):
        meta = self.db.execute('SELECT spec,height,head FROM meta WHERE id=1').fetchone()
        if meta is None or meta[0] != spec_id(self.spec): raise ValueError('Database identity mismatch')
        state, height, head, timestamp = initial_state(), 0, genesis(self.spec), 0
        matched = self.checkpoint is None
        if self.checkpoint is not None:
            if type(self.checkpoint) is not dict or set(self.checkpoint) != {'height', 'hash'}: raise ValueError('Invalid checkpoint')
            integer(self.checkpoint['height']); hexvalue(self.checkpoint['hash'])
            matched = self.checkpoint == {'height': 0, 'hash': head}
        for row_height, body, certificate in self.db.execute('SELECT height,body,certificate FROM blocks ORDER BY height'):
            block, cert = json.loads(body), json.loads(certificate)
            if row_height != height+1: raise ValueError('Stored height gap')
            state = validate_proposal(block, self.spec, state, height+1, head, timestamp)
            verify_certificate(self.spec, block, cert)
            height, head, timestamp = block['height'], digest('block', block), block['timestamp']
            if self.checkpoint == {'height': height, 'hash': head}: matched = True
        if (height, head) != (meta[1], meta[2]): raise ValueError('Stored head mismatch')
        if not matched: raise ValueError('Trusted checkpoint missing or mismatched')
        return {'state': state, 'height': height, 'hash': head, 'timestamp': timestamp}

    def snapshot(self):
        self.db.execute('BEGIN')
        try:
            value = self._replay()
            self.db.commit()
            return value
        except BaseException:
            self.db.rollback(); raise

    def vote(self, key, block, now):
        validator = public(key)
        if validator not in self.spec['validators']: raise ValueError('Signer outside committee')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            state = self._replay()
            validate_proposal(block, self.spec, state['state'], state['height']+1,
                              state['hash'], state['timestamp'], now=now)
            block_hash = digest('block', block)
            existing = self.db.execute('SELECT hash FROM locks WHERE validator=? AND height=?', (validator, block['height'])).fetchone()
            if existing and existing[0] != block_hash: raise ValueError('Conflicting vote refused')
            if not existing:
                self.db.execute('INSERT INTO locks VALUES(?,?,?)', (validator, block['height'], block_hash))
            # Persist the lock before releasing any signature.
            self.db.commit()
        except BaseException:
            self.db.rollback(); raise
        return {'validator': validator, 'signature': key.sign(vote_message(self.spec, block)).hex()}

    def commit(self, block, votes):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            snapshot = self._replay()
            validate_proposal(block, self.spec, snapshot['state'], snapshot['height']+1,
                              snapshot['hash'], snapshot['timestamp'])
            verify_certificate(self.spec, block, votes)
            self.db.execute('INSERT INTO blocks VALUES(?,?,?)', (block['height'], canonical(block).decode(), canonical(votes).decode()))
            self.db.execute('UPDATE meta SET height=?, head=? WHERE id=1', (block['height'], digest('block', block)))
            self.db.commit()
        except BaseException:
            self.db.rollback(); raise

    def backup(self, destination):
        fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        target = sqlite3.connect(destination)
        try: self.db.backup(target)
        finally: target.close()

    def close(self): self.db.close()
    def __enter__(self): return self
    def __exit__(self, *args): self.close()
