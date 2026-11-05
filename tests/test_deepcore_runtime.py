import pytest

from CORE.deepcore_runtime import DeepCoreLedger, Transaction, merkle_root, ZERO_HASH


@pytest.fixture
def ledger_and_secrets():
    validators = ["validator_A", "validator_B", "validator_C", "validator_D"]
    secrets = {v: f"development-secret:{v}".encode() for v in validators}
    return DeepCoreLedger(validators), secrets


def signed_tx(secrets, **overrides):
    values = {
        "sender": "validator_A",
        "receiver": "validator_B",
        "amount": 100,
        "fee": 1,
        "nonce": 1,
        "signer": "validator_A",
    }
    values.update(overrides)
    return Transaction(**values).sign_dev(secrets[values["signer"]])


def test_bft_quorum(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    assert ledger.f == 1
    assert ledger.quorum == 3
    ledger.append(signed_tx(secrets), secrets)
    with pytest.raises(ValueError, match="BFT quorum not met"):
        ledger.commit(["validator_A", "validator_B"])


def test_duplicate_votes_do_not_increase_quorum(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    ledger.append(signed_tx(secrets), secrets)
    with pytest.raises(ValueError, match="BFT quorum not met"):
        ledger.commit(["validator_A", "validator_A", "validator_B"])


def test_forged_signature_rejected(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    tx = Transaction("validator_A", "validator_B", 100, 1, 1, "validator_A").sign_dev(secrets["validator_B"])
    ok, reason = ledger.validate(tx, secrets)
    assert not ok
    assert "signature" in reason


def test_nonce_replay_rejected(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    tx = signed_tx(secrets)
    ledger.append(tx, secrets)
    ledger.commit(["validator_A", "validator_B", "validator_C"])
    ok, reason = ledger.validate(tx, secrets)
    assert not ok
    assert "nonce" in reason


def test_insufficient_balance_rejected(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    tx = signed_tx(secrets, amount=2_000_000)
    ok, reason = ledger.validate(tx, secrets)
    assert not ok
    assert "insufficient balance" in reason


def test_unknown_vote_rejected(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    ledger.append(signed_tx(secrets), secrets)
    with pytest.raises(ValueError, match="unknown validator vote"):
        ledger.commit(["validator_A", "validator_B", "intruder"])


@pytest.mark.parametrize("voters, expected", [
    ([], False),
    (["validator_A"], False),
    (["validator_A", "validator_A"], False),
    (["validator_A", "validator_B"], True),
    (["validator_A", "validator_B", "validator_C"], True),
    (["validator_B", "validator_C", "validator_D"], False),
    (["validator_A", "validator_B", "intruder"], False),
])
def test_weighted_quorum(voters, expected):
    weighted = DeepCoreLedger(
        ["validator_A", "validator_B", "validator_C", "validator_D"],
        weights={"validator_A": 4, "validator_B": 1, "validator_C": 1, "validator_D": 1},
    )
    # This predicate checks weight only: A+B has 5/7 of the weight.
    # prepare_block/commit separately enforce the distinct-validator count.
    assert weighted.weighted_quorum_met(voters) is expected


def test_weighted_commit_requires_both_count_and_weight(ledger_and_secrets):
    _, secrets = ledger_and_secrets
    ledger = DeepCoreLedger(
        list(secrets),
        weights={"validator_A": 4, "validator_B": 1, "validator_C": 1, "validator_D": 1},
    )
    event = ledger.append(signed_tx(secrets), secrets)
    initial_state_root = ledger.state_root()

    # Weight passes, but two unique validators cannot satisfy the count quorum.
    for voters in (["validator_A", "validator_B"],
                   ["validator_A", "validator_B", "validator_B"]):
        with pytest.raises(ValueError, match="BFT quorum not met"):
            ledger.commit(voters)
        assert ledger.state_root() == initial_state_root
        assert ledger.events == [event] and ledger.blocks == []

    # Three unique validators still fail when they hold only 3/7 of the weight.
    with pytest.raises(ValueError, match="weighted quorum not met"):
        ledger.commit(["validator_B", "validator_C", "validator_D"])
    assert ledger.state_root() == initial_state_root
    assert ledger.events == [event] and ledger.blocks == []

    block = ledger.commit(["validator_A", "validator_B", "validator_C"])
    assert block.height == 1
    assert ledger.events == []
    assert ledger.replay() == ledger.state


def test_merkle_root_changes_when_leaf_changes():
    original = merkle_root(["a", "b", "c"])
    modified = merkle_root(["a", "b", "d"])
    assert original != modified


def test_block_tampering_detected(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    ledger.append(signed_tx(secrets), secrets)
    block = ledger.commit(["validator_A", "validator_B", "validator_C"])
    assert ledger.verify_block(block, ZERO_HASH)
    tampered = type(block)(
        height=block.height,
        previous_hash=block.previous_hash,
        state_root=ZERO_HASH,
        event_root=block.event_root,
        validator_votes=block.validator_votes,
        events=block.events,
        block_hash=block.block_hash,
    )
    assert not ledger.verify_block(tampered, ZERO_HASH)


def test_replay_matches_live_state(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    ledger.append(signed_tx(secrets, amount=100), secrets)
    ledger.commit(["validator_A", "validator_B", "validator_C"])
    tx2 = signed_tx(secrets, amount=200, nonce=2)
    ledger.append(tx2, secrets)
    ledger.commit(["validator_A", "validator_B", "validator_C"])
    assert ledger.replay() == ledger.state


def test_invalid_amount_risk_rejected(ledger_and_secrets):
    ledger, secrets = ledger_and_secrets
    tx = signed_tx(secrets, amount=0)
    ok, reason = ledger.validate(tx, secrets)
    assert not ok
    assert "invalid amount" in reason
