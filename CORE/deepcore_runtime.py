#!/usr/bin/env python3
"""DeepCore Systems Enterprise deterministic ledger runtime.

Reference implementation of the mathematical model in
``docs/DEEPCORE-BLOCKCHAIN-MATHEMATICS.md``.

HMAC-SHA256 remains available only as a development compatibility path.
Ed25519 is the production-oriented asymmetric signature path. Validator
public keys can be lifecycle-managed through ``ValidatorKeyRegistry``.
Private-key custody, HSM integration, consensus networking, and durable
external key-state persistence remain separate controls.

Run:
    python CORE/deepcore_runtime.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

ZERO_HASH = hashlib.sha256(b"").hexdigest()


def canonical(obj: Any) -> bytes:
    """Canonical JSON serialization used by every commitment."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_obj(obj: Any) -> str:
    return sha256_bytes(canonical(obj))


def merkle_root(leaves: list[str]) -> str:
    """Binary Merkle root; odd levels duplicate the final leaf."""
    if not leaves:
        return ZERO_HASH
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [sha256_bytes((level[i] + level[i + 1]).encode()) for i in range(0, len(level), 2)]
    return level[0]


@dataclass(frozen=True)
class Transaction:
    sender: str
    receiver: str
    amount: int
    fee: int
    nonce: int
    signer: str
    signature: str = ""

    def unsigned(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "fee": self.fee,
            "nonce": self.nonce,
            "signer": self.signer,
        }

    def sign_dev(self, secret: bytes) -> "Transaction":
        """Development-only HMAC authentication placeholder."""
        sig = hmac.new(secret, canonical(self.unsigned()), hashlib.sha256).hexdigest()
        return Transaction(**self.unsigned(), signature=sig)

    def verify_dev(self, secret: bytes) -> bool:
        expected = hmac.new(secret, canonical(self.unsigned()), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)

    def sign_ed25519(self, identity: Any) -> "Transaction":
        """Sign canonical transaction bytes with a DeepCore Ed25519 identity."""
        sig = identity.sign(canonical(self.unsigned()))
        return Transaction(**self.unsigned(), signature=sig)

    def verify_ed25519(self, public_key: bytes) -> bool:
        """Verify the transaction against an Ed25519 public key."""
        from CORE.deepcore_crypto import verify

        return verify(public_key, canonical(self.unsigned()), self.signature)


@dataclass(frozen=True)
class Event:
    transaction: Transaction

    @property
    def event_id(self) -> str:
        return sha256_obj({"transaction": self.transaction.unsigned(), "signature": self.transaction.signature})


@dataclass(frozen=True)
class Block:
    height: int
    previous_hash: str
    state_root: str
    event_root: str
    validator_votes: tuple[str, ...]
    events: tuple[Event, ...]
    block_hash: str


class DeepCoreLedger:
    """Deterministic event-sourced ledger with BFT-style quorum checks."""

    def __init__(self, validators: list[str], weights: dict[str, int] | None = None, max_byzantine: int | None = None):
        if not validators or len(set(validators)) != len(validators):
            raise ValueError("validators must be non-empty and unique")
        self.validators = tuple(sorted(validators))
        self.weights = weights or {v: 1 for v in self.validators}
        if set(self.weights) != set(self.validators) or any(w <= 0 for w in self.weights.values()):
            raise ValueError("weights must contain every validator and be positive")
        self.f = (len(self.validators) - 1) // 3 if max_byzantine is None else max_byzantine
        if len(self.validators) < 3 * self.f + 1:
            raise ValueError("BFT safety requires N >= 3f + 1")
        self.events: list[Event] = []
        self.blocks: list[Block] = []
        self.state: dict[str, dict[str, int]] = {
            v: {"balance": 1_000_000, "nonce": 0} for v in self.validators
        }

    @property
    def quorum(self) -> int:
        return 2 * self.f + 1

    @property
    def total_weight(self) -> int:
        return sum(self.weights.values())

    def weighted_quorum_met(self, voters: list[str]) -> bool:
        unique = set(voters)
        if not unique.issubset(self.weights):
            return False
        return sum(self.weights[v] for v in unique) * 3 >= self.total_weight * 2

    @staticmethod
    def ssil_risk(tx: Transaction) -> tuple[float, str]:
        """Small deterministic risk model for runtime demonstration."""
        if tx.amount <= 0 or tx.fee < 0:
            return 1.0, "reject"
        size_factor = min(len(canonical(tx.unsigned())) / 400.0, 1.0)
        amount_factor = min(tx.amount / 1_000_000.0, 1.0)
        fee_factor = min(tx.fee / 100_000.0, 1.0)
        score = round(0.20 * size_factor + 0.50 * amount_factor + 0.30 * fee_factor, 6)
        category = "accept" if score < 0.30 else "review" if score < 0.70 else "reject"
        return score, category

    def validate(self, tx: Transaction, secrets: dict[str, bytes]) -> tuple[bool, str]:
        if tx.signer not in self.validators:
            return False, "unknown signer"
        if tx.sender not in self.state or tx.receiver == "":
            return False, "invalid account"
        if tx.sender != tx.signer:
            return False, "signer must match sender in this reference model"
        secret = secrets.get(tx.signer)
        if secret is None or not tx.verify_dev(secret):
            return False, "invalid development signature"
        return self._validate_transaction_state(tx)

    def validate_ed25519(self, tx: Transaction, registry: Any) -> tuple[bool, str]:
        """Validate a transaction using the active public key for its signer."""
        if tx.signer not in self.validators:
            return False, "unknown signer"
        if tx.sender not in self.state or tx.receiver == "":
            return False, "invalid account"
        if tx.sender != tx.signer:
            return False, "signer must match sender in this reference model"
        if not registry.verify(tx.signer, canonical(tx.unsigned()), tx.signature):
            return False, "invalid Ed25519 signature or inactive key"
        return self._validate_transaction_state(tx)

    def _validate_transaction_state(self, tx: Transaction) -> tuple[bool, str]:
        expected_nonce = self.state[tx.sender]["nonce"] + 1
        if tx.nonce != expected_nonce:
            return False, f"invalid nonce: expected {expected_nonce}"
        if tx.amount <= 0 or tx.fee < 0:
            return False, "invalid amount or fee"
        if self.state[tx.sender]["balance"] < tx.amount + tx.fee:
            return False, "insufficient balance"
        score, category = self.ssil_risk(tx)
        if category == "reject":
            return False, f"SSIL reject: {score}"
        return True, f"valid; SSIL={category}:{score}"

    def append(self, tx: Transaction, secrets: dict[str, bytes]) -> Event:
        ok, reason = self.validate(tx, secrets)
        if not ok:
            raise ValueError(reason)
        event = Event(tx)
        self.events.append(event)
        return event

    def append_ed25519(self, tx: Transaction, registry: Any) -> Event:
        """Append only after active Ed25519 authentication and state checks."""
        ok, reason = self.validate_ed25519(tx, registry)
        if not ok:
            raise ValueError(reason)
        event = Event(tx)
        self.events.append(event)
        return event

    def _apply(self, event: Event, state: dict[str, dict[str, int]]) -> None:
        tx = event.transaction
        sender = state[tx.sender]
        receiver = state.setdefault(tx.receiver, {"balance": 0, "nonce": 0})
        sender["balance"] -= tx.amount + tx.fee
        sender["nonce"] += 1
        receiver["balance"] += tx.amount

    def state_root(self, state: dict[str, dict[str, int]] | None = None) -> str:
        return sha256_obj(state if state is not None else self.state)

    @staticmethod
    def _block_body(block: Block) -> dict[str, Any]:
        return {
            "height": block.height,
            "previous_hash": block.previous_hash,
            "state_root": block.state_root,
            "event_root": block.event_root,
            "validator_votes": list(block.validator_votes),
        }

    def commit(self, voters: list[str]) -> Block:
        if not self.events:
            raise ValueError("no pending events")
        unique = set(voters)
        if len(unique) < self.quorum:
            raise ValueError(f"BFT quorum not met: need {self.quorum} unique voters")
        if not unique.issubset(self.validators):
            raise ValueError("unknown validator vote")
        if not self.weighted_quorum_met(voters):
            raise ValueError("weighted quorum not met")

        pending = tuple(self.events)
        candidate = {k: dict(v) for k, v in self.state.items()}
        for event in pending:
            self._apply(event, candidate)

        previous_hash = self.blocks[-1].block_hash if self.blocks else ZERO_HASH
        event_root = merkle_root([e.event_id for e in pending])
        next_root = self.state_root(candidate)
        body = {
            "height": len(self.blocks) + 1,
            "previous_hash": previous_hash,
            "state_root": next_root,
            "event_root": event_root,
            "validator_votes": sorted(unique),
        }
        block_hash = sha256_obj(body)
        block = Block(
            height=body["height"],
            previous_hash=previous_hash,
            state_root=next_root,
            event_root=event_root,
            validator_votes=tuple(sorted(unique)),
            events=pending,
            block_hash=block_hash,
        )
        self.state = candidate
        self.blocks.append(block)
        self.events.clear()
        return block

    def replay(self) -> dict[str, dict[str, int]]:
        """Reconstruct and verify state exclusively from committed blocks."""
        replayed = {v: {"balance": 1_000_000, "nonce": 0} for v in self.validators}
        previous_hash = ZERO_HASH

        for expected_height, block in enumerate(self.blocks, start=1):
            if block.height != expected_height:
                raise ValueError("invalid block height during replay")
            if not self.verify_block(block, previous_hash):
                raise ValueError(f"invalid block commitment at height {block.height}")
            if merkle_root([event.event_id for event in block.events]) != block.event_root:
                raise ValueError(f"event root mismatch at height {block.height}")
            for event in block.events:
                self._apply(event, replayed)
            if self.state_root(replayed) != block.state_root:
                raise ValueError(f"state root mismatch at height {block.height}")
            previous_hash = block.block_hash

        return replayed

    def verify_block(self, block: Block, previous_hash: str) -> bool:
        body = self._block_body(block)
        return block.previous_hash == previous_hash and sha256_obj(body) == block.block_hash


def main() -> None:
    from CORE.deepcore_crypto import Ed25519Identity
    from CORE.deepcore_key_registry import ValidatorKeyRegistry

    validators = ["validator_A", "validator_B", "validator_C", "validator_D"]
    identities = {v: Ed25519Identity.generate() for v in validators}
    registry = ValidatorKeyRegistry()
    for validator, identity in identities.items():
        registry.register(validator, identity.public_key_bytes)

    ledger = DeepCoreLedger(validators)
    tx = Transaction("validator_A", "validator_B", 100_000, 1_000, 1, "validator_A")
    tx = tx.sign_ed25519(identities["validator_A"])
    event = ledger.append_ed25519(tx, registry)
    block = ledger.commit(["validator_A", "validator_B", "validator_C"])

    assert ledger.quorum == 3
    assert ledger.verify_block(block, ZERO_HASH)
    assert block.event_root == merkle_root([event.event_id])
    assert block.state_root == ledger.state_root()
    assert ledger.replay() == ledger.state
    assert ledger.state["validator_A"] == {"balance": 899_000, "nonce": 1}
    assert ledger.state["validator_B"] == {"balance": 1_100_000, "nonce": 0}

    registry.revoke("validator_A")
    revoked_ok, revoked_reason = ledger.validate_ed25519(tx, registry)
    assert not revoked_ok and "inactive" in revoked_reason

    score, category = ledger.ssil_risk(tx)
    print("=== DeepCore Runtime Evidence ===")
    print(f"validators={len(validators)} f={ledger.f} quorum={ledger.quorum}")
    print(f"block_height={block.height}")
    print(f"event_id={event.event_id}")
    print(f"event_root={block.event_root}")
    print(f"state_root={block.state_root}")
    print(f"block_hash={block.block_hash}")
    print(f"ssil_score={score} category={category}")
    print("ed25519_signature_verified=True")
    print("key_registry_revocation_verified=True")
    print(f"revoked_key_rejected={not revoked_ok}")
    print(f"chain_commitment_verified={ledger.verify_block(block, ZERO_HASH)}")
    print("replay_state_verified=True")
    print("runtime_status=REFERENCE_IMPLEMENTATION_VERIFIED")
    print("crypto_note=Ed25519 is integrated; private-key custody, HSM, rotation governance, and consensus networking remain separate controls.")


if __name__ == "__main__":
    main()
