import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from protocol import *
from storage import Ledger
from key_store import create_key, load_key


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'chain.sqlite'
        self.keys = [Ed25519PrivateKey.generate() for _ in range(4)]
        self.writer = Ed25519PrivateKey.generate()
        self.spec = {'version': 2, 'network': 'bkillings-test-v2', 'epoch': 0,
                     'validators': [public(k) for k in self.keys], 'faults': 1,
                     'writers': [public(self.writer)]}
        self.ledger = Ledger(self.path, self.spec, create=True)
    def tearDown(self):
        self.ledger.close(); self.tmp.cleanup()
    def block(self, payload=None):
        snap = self.ledger.snapshot()
        tx = sign_transaction(self.writer, self.spec, snap['height']+1, 1000,
                              'observation', payload or {'v': 1})
        return propose(self.spec, snap['state'], snap['height']+1, snap['hash'], snap['timestamp'], [tx], 1000)
    def cert(self, block):
        return [self.ledger.vote(k, block, 1000) for k in self.keys[:3]]
    def test_commit_restart(self):
        b = self.block(); self.ledger.commit(b, self.cert(b))
        with Ledger(self.path, self.spec) as ledger:
            self.assertEqual(ledger.snapshot()['height'], 1)
    def test_cross_network(self):
        b = self.block(); other = copy.deepcopy(self.spec); other['network'] = 'other'
        with self.assertRaises(ValueError): transition(initial_state(), b['transactions'], other, 1000)
    def test_signature_domain_tampering(self):
        b = self.block(); b['transactions'][0]['body']['payload']['v'] = 7
        with self.assertRaises(ValueError): self.ledger.vote(self.keys[0], b, 1000)
    def test_clock_independent_replay(self):
        b = self.block(); self.ledger.commit(b, self.cert(b))
        with patch('time.time', side_effect=AssertionError('clock consulted')):
            self.assertEqual(self.ledger.snapshot()['height'], 1)
    def test_future_admission(self):
        with self.assertRaises(ValueError): self.ledger.vote(self.keys[0], self.block(), 0)
    def test_timestamp_vs_block(self):
        b = self.block(); tx = sign_transaction(self.writer, self.spec, 1, 2000, 'x', {})
        with self.assertRaises(ValueError): transition(initial_state(), [tx], self.spec, 1000)
    def test_nonce_replay(self):
        b = self.block(); self.ledger.commit(b, self.cert(b))
        with self.assertRaises(ValueError): transition(self.ledger.snapshot()['state'], b['transactions'], self.spec, 1000)
    def test_unknown_writer(self):
        tx = sign_transaction(self.keys[0], self.spec, 1, 1000, 'x', {})
        with self.assertRaises(ValueError): transition(initial_state(), [tx], self.spec, 1000)
    def test_insufficient_quorum(self):
        b = self.block()
        with self.assertRaises(ValueError): self.ledger.commit(b, self.cert(b)[:2])
        self.assertEqual(self.ledger.snapshot()['height'], 0)
    def test_duplicate_voter(self):
        b = self.block(); votes = self.cert(b)
        with self.assertRaises(ValueError): verify_certificate(self.spec, b, [votes[0]]*3)
    def test_forged_vote(self):
        b = self.block(); votes = self.cert(b); votes[0]['signature'] = '00'*64
        with self.assertRaises(ValueError): verify_certificate(self.spec, b, votes)
    def test_durable_no_double_vote(self):
        b = self.block(); original = self.ledger.vote(self.keys[0], b, 1000)
        with Ledger(self.path, self.spec) as ledger:
            self.assertEqual(ledger.vote(self.keys[0], b, 1000), original)
            with self.assertRaises(ValueError): ledger.vote(self.keys[0], self.block({'v': 2}), 1000)
    def test_wrong_committee(self):
        spec = copy.deepcopy(self.spec); spec['validators'][0] = public(Ed25519PrivateKey.generate())
        with self.assertRaises(ValueError): Ledger(self.path, spec)
    def test_backup_restore_checkpoint(self):
        b = self.block(); self.ledger.commit(b, self.cert(b))
        backup = Path(self.tmp.name)/'backup.sqlite'; self.ledger.backup(backup)
        checkpoint = {'height': 1, 'hash': digest('block', b)}
        with Ledger(backup, self.spec, checkpoint=checkpoint) as restored:
            self.assertEqual(restored.snapshot(), self.ledger.snapshot())
    def test_truncation_detected(self):
        b = self.block(); self.ledger.commit(b, self.cert(b))
        self.ledger.db.execute('DELETE FROM blocks')
        with self.assertRaises(ValueError): self.ledger.snapshot()
    def test_checkpoint_detects_coordinated_truncation(self):
        b = self.block(); self.ledger.commit(b, self.cert(b))
        self.ledger.db.execute('DELETE FROM blocks')
        self.ledger.db.execute('UPDATE meta SET height=0,head=?', (genesis(self.spec),))
        with self.assertRaises(ValueError): Ledger(self.path, self.spec, checkpoint={'height':1,'hash':digest('block',b)})
    def test_missing_db_not_initialized(self):
        with self.assertRaises(ValueError): Ledger(Path(self.tmp.name)/'missing', self.spec)
    def test_failed_insert_rollback(self):
        b = self.block(); votes = self.cert(b)
        self.ledger.db.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON blocks BEGIN SELECT RAISE(ABORT,'injected'); END")
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError): self.ledger.commit(b, votes)
        self.assertEqual(self.ledger.snapshot()['height'], 0)
    def test_strict_encoding(self):
        for value in (float('nan'), 1.0, 2**63, {1: 'bad'}, '\ud800'):
            with self.assertRaises((ValueError, UnicodeError)): canonical(value)
    def test_key_encryption(self):
        path = Path(self.tmp.name)/'validator.pem'; password = b'unit-test-password-long'
        identity = create_key(path, password)
        self.assertEqual(public(load_key(path, password)), identity)
        self.assertIn(b'ENCRYPTED PRIVATE KEY', path.read_bytes())
        with self.assertRaises(ValueError): load_key(path, b'wrong-password-long')
        with self.assertRaises(FileExistsError): create_key(path, password)
    def test_key_permission_rejection(self):
        path = Path(self.tmp.name)/'key.pem'; password = b'unit-test-password-long'
        create_key(path, password); path.chmod(0o644)
        with self.assertRaises(ValueError): load_key(path, password)
    def test_symlink_key_rejection(self):
        path = Path(self.tmp.name)/'key.pem'; password = b'unit-test-password-long'
        create_key(path, password); link = Path(self.tmp.name)/'link'; link.symlink_to(path)
        with self.assertRaises(OSError): load_key(link, password)
    def test_batch_limit(self):
        tx = self.block()['transactions'][0]
        with self.assertRaises(ValueError): transition(initial_state(), [tx]*101, self.spec, 1000)
    def test_bool_nonce_rejected(self):
        tx = sign_transaction(self.writer, self.spec, True, 1000, 'x', {})
        with self.assertRaises(ValueError): transition(initial_state(), [tx], self.spec, 1000)


if __name__ == '__main__': unittest.main()
