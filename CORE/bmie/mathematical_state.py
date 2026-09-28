"""Deterministic mathematical state primitives for BMIE v0.1."""
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import hashlib
import json

getcontext().prec = 28


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResourceState:
    initial: Decimal
    available: Decimal
    consumed: Decimal
    reserve: Decimal
    intervals_remaining: int

    def verify_conservation(self) -> bool:
        return self.initial == self.available + self.consumed + self.reserve

    def state_root(self) -> str:
        return canonical_hash(asdict(self))

    def transition(self, consumption: Decimal) -> "ResourceState":
        if consumption < 0:
            raise ValueError("consumption cannot be negative")
        if consumption > self.available:
            raise ValueError("resource capacity exceeded")
        if self.intervals_remaining <= 0:
            raise ValueError("no execution intervals remain")
        result = ResourceState(
            initial=self.initial,
            available=self.available - consumption,
            consumed=self.consumed + consumption,
            reserve=self.reserve,
            intervals_remaining=self.intervals_remaining - 1,
        )
        if not result.verify_conservation():
            raise ValueError("resource conservation invariant violated")
        return result
