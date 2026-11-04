import copy
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from protocol import public, sign_transaction, propose, digest
from storage import Ledger


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'chain.sqlite'
        self.keys = [Ed25519PrivateKey.generate() for _ in range(4)]
        self.writers = [Ed25519PrivateKey.generate() for _ in range(3)]
        self.spec = {'version':2, 'network':'incremental-test', 'epoch':0,
                     'validators':[public(k) for k in self.keys], 'faults':1,
                     'writers':[public(k) for k in self.writers]}
        self.ledger = Ledger(self.path, self.spec, create=True)
    def tearDown(self):
        self.ledger.close(); self.tmp.cleanup()
    def next_block(self, ledger=None, writer=0):
        ledger = ledger or self.ledger
        snap = ledger.snapshot(); key = self.writers[writer]
        nonce = snap['state']['nonces'].get(public(key),0)+1
        tx = sign_transaction(key,self.spec,nonce,1000+snap['height'],'TEST',{'n':nonce})
        return propose(self.spec,snap['state'],snap['height']+1,snap['hash'],snap['timestamp'],[tx],1000+snap['height'])
    def append(self, ledger=None, writer=0):
        ledger = ledger or self.ledger
        block = self.next_block(ledger,writer)
        votes = [ledger.vote(k,block,2000) for k in self.keys[:3]]
        ledger.commit(block,votes)
        return block
    def test_cached_operations_do_not_replay(self):
        with patch.object(self.ledger,'_replay',side_effect=AssertionError('unexpected full replay')):
            for _ in range(3): self.append()
        self.assertEqual(self.ledger.snapshot(),self.ledger.snapshot(full_audit=True))
    def test_full_audit_is_unconditional(self):
        self.append()
        with patch.object(self.ledger,'_replay',wraps=self.ledger._replay) as replay:
            self.ledger.snapshot(full_audit=True)
            self.assertEqual(replay.call_count,1)
    def test_differential_randomized_history(self):
        rng = random.Random(20260926)
        path = Path(self.tmp.name)/'reference.sqlite'
        with Ledger(path,self.spec,create=True,incremental=False) as reference:
            for _ in range(20):
                writer = rng.randrange(3)
                block = self.next_block(writer=writer)
                votes = [self.ledger.vote(k,block,2000) for k in self.keys[:3]]
                self.ledger.commit(block,votes); reference.commit(block,votes)
                self.assertEqual(self.ledger.snapshot(),reference.snapshot())
                self.assertEqual(self.ledger.snapshot(),self.ledger.snapshot(full_audit=True))
    def test_external_writer_forces_replay(self):
        with Ledger(self.path,self.spec) as other:
            self.append(other)
        with patch.object(self.ledger,'_replay',wraps=self.ledger._replay) as replay:
            self.assertEqual(self.ledger.snapshot()['height'],1)
            self.assertEqual(replay.call_count,1)
    def test_same_connection_corruption_detected(self):
        self.append()
        self.ledger.db.execute("UPDATE blocks SET certificate='[]' WHERE height=1")
        with self.assertRaises(ValueError): self.ledger.snapshot()
    def test_other_connection_corruption_detected(self):
        self.append()
        with Ledger(self.path,self.spec) as other:
            other.db.execute("UPDATE blocks SET certificate='[]' WHERE height=1")
        with self.assertRaises(ValueError): self.ledger.snapshot()
    def test_returned_state_cannot_modify_cache(self):
        self.append(); snapshot = self.ledger.snapshot(); expected = copy.deepcopy(snapshot)
        snapshot['state']['nonces'].clear(); snapshot['height'] = 999
        self.assertEqual(self.ledger.snapshot(),expected)
    def test_restart_always_audits(self):
        self.append()
        with patch.object(Ledger,'_replay',side_effect=ValueError('audit forced')):
            with self.assertRaisesRegex(ValueError,'audit forced'): Ledger(self.path,self.spec)
    def test_external_commit_after_snapshot_release(self):
        with Ledger(self.path,self.spec) as other:
            publish = self.ledger._publish
            def interleave(value,token):
                self.append(other)
                publish(value,token)
            with patch.object(self.ledger,'_publish',side_effect=interleave):
                self.assertEqual(self.ledger.snapshot()['height'],0)
        # The old snapshot token must not be labeled with the newer data version.
        self.assertEqual(self.ledger.snapshot()['height'],1)
    def test_changed_checkpoint_forces_validation(self):
        self.append()
        self.ledger.checkpoint = {'height':1,'hash':'0'*64}
        with self.assertRaises(ValueError): self.ledger.snapshot()
    def test_external_commit_during_read_snapshot(self):
        with Ledger(self.path,self.spec) as other:
            original = self.ledger._cache_token
            calls = 0
            def interleave():
                nonlocal calls
                token = original()
                calls += 1
                if calls == 1:
                    self.append(other)
                return token
            with patch.object(self.ledger,'_cache_token',side_effect=interleave):
                self.assertEqual(self.ledger.snapshot()['height'],0)
        self.assertEqual(self.ledger.snapshot()['height'],1)
    def test_changed_spec_forces_validation(self):
        self.ledger.spec['network'] = 'other'
        with self.assertRaises(ValueError): self.ledger.snapshot()
    def test_unexpected_trigger_side_effect_rolls_back(self):
        block = self.next_block()
        votes = [self.ledger.vote(k,block,2000) for k in self.keys[:3]]
        self.ledger.db.execute("CREATE TRIGGER alter_history AFTER INSERT ON blocks BEGIN UPDATE blocks SET certificate='[]' WHERE height=NEW.height; END")
        with self.assertRaisesRegex(ValueError,'Unexpected SQL side effects'):
            self.ledger.commit(block,votes)
        self.assertEqual(self.ledger.snapshot(full_audit=True)['height'],0)
    def test_failed_commit_does_not_advance_cache(self):
        self.append(); block = self.next_block()
        votes = [self.ledger.vote(k,block,2000) for k in self.keys[:3]]
        votes[0]['signature'] = '00'*64
        with self.assertRaises(ValueError): self.ledger.commit(block,votes)
        self.assertEqual(self.ledger.snapshot()['height'],1)
        self.assertEqual(self.ledger.snapshot(),self.ledger.snapshot(full_audit=True))


if __name__ == '__main__': unittest.main()
