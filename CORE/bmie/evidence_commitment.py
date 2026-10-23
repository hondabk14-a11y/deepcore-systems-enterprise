"""Cryptographic evidence commitments for BMIE results."""
from typing import Iterable
from .mathematical_state import canonical_hash


def merkle_root(items: Iterable[object]) -> str:
    hashes = [canonical_hash(item) for item in items]
    if not hashes:
        return canonical_hash("")
    while len(hashes) > 1:
        if len(hashes) % 2:
            hashes.append(hashes[-1])
        hashes = [canonical_hash(hashes[i] + hashes[i + 1]) for i in range(0, len(hashes), 2)]
    return hashes[0]


def evidence_root(inputs: object, computation: object, outputs: object, tests: object) -> str:
    return merkle_root([inputs, computation, outputs, tests])
