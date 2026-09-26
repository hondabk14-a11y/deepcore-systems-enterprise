"""Version 2 protocol: strict encoding, domain binding, deterministic replay."""
import hashlib
import json
from copy import deepcopy
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

VERSION = 2
MAX_BYTES = 1_048_576
MAX_TX = 100
DRIFT = 300


def canonical(value):
    def check(v, depth=0):
        if depth > 32: raise ValueError('Nesting limit')
        if v is None or type(v) is bool: return
        if type(v) is int and -(2**63) <= v < 2**63: return
        if type(v) is str:
            v.encode('utf-8')
            return
        if type(v) is list:
            for x in v: check(x, depth+1)
            return
        if type(v) is dict and all(type(k) is str for k in v):
            for k,x in v.items(): check(k, depth+1); check(x, depth+1)
            return
        raise ValueError('Unsupported canonical value')
    check(value)
    result = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    if len(result) > MAX_BYTES: raise ValueError('Encoding size limit')
    return result


def digest(domain, value):
    return hashlib.sha256(canonical(['BKILLINGS', VERSION, domain, value])).hexdigest()


def exact(obj, fields):
    if type(obj) is not dict or set(obj) != set(fields.split()): raise ValueError('Invalid fields')


def integer(value, minimum=0):
    if type(value) is not int or not minimum <= value < 2**63: raise ValueError('Invalid integer')


def hexvalue(value, size=32):
    if type(value) is not str or len(value) != size*2 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Invalid hexadecimal value')


def public(key):
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def validate_spec(spec):
    exact(spec, 'version network epoch validators faults writers')
    if type(spec['version']) is not int or spec['version'] != VERSION: raise ValueError('Protocol version')
    if type(spec['network']) is not str or not spec['network'] or len(spec['network']) > 128: raise ValueError('Network ID')
    integer(spec['epoch']); integer(spec['faults'])
    for field in ('validators', 'writers'):
        values = spec[field]
        if type(values) is not list or not values or len(values) > 128: raise ValueError('Invalid registry')
        for key in values: hexvalue(key)
        if len(set(values)) != len(values): raise ValueError('Duplicate identity')
    if len(spec['validators']) < 3*spec['faults']+1: raise ValueError('Unsafe fault threshold')
    canonical(spec)


def spec_id(spec):
    validate_spec(spec)
    return digest('genesis-spec', spec)


def initial_state():
    return {'nonces': {}, 'counters': {}, 'event_root': digest('empty-events', [])}


def genesis(spec):
    return digest('genesis', {'spec': spec_id(spec), 'state': initial_state()})


def sign_transaction(key, spec, nonce, timestamp, event_type, payload):
    body = {'version': VERSION, 'spec': spec_id(spec), 'sender': public(key),
            'nonce': nonce, 'timestamp': timestamp, 'event_type': event_type, 'payload': deepcopy(payload)}
    signature = key.sign(canonical(['BKILLINGS', VERSION, 'transaction', body])).hex()
    return {'body': body, 'signature': signature}


def verify_signature(key, signature, message):
    hexvalue(key); hexvalue(signature, 64)
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(key)).verify(bytes.fromhex(signature), message)
    except InvalidSignature as exc:
        raise ValueError('Invalid signature') from exc


def transition(state, txs, spec, block_time):
    integer(block_time)
    if type(txs) is not list or not 1 <= len(txs) <= MAX_TX: raise ValueError('Batch size')
    canonical(txs)
    result = deepcopy(state)
    identity = spec_id(spec)
    for tx in txs:
        exact(tx, 'body signature')
        body = tx['body']
        exact(body, 'version spec sender nonce timestamp event_type payload')
        if type(body['version']) is not int or body['version'] != VERSION or body['spec'] != identity: raise ValueError('Transaction domain')
        if body['sender'] not in spec['writers']: raise ValueError('Unauthorized writer')
        integer(body['nonce'], 1); integer(body['timestamp'])
        if body['timestamp'] > block_time + DRIFT: raise ValueError('Transaction ahead of block')
        if type(body['event_type']) is not str or not 1 <= len(body['event_type']) <= 128: raise ValueError('Event type')
        if type(body['payload']) is not dict: raise ValueError('Payload object required')
        if body['nonce'] != result['nonces'].get(body['sender'], 0)+1: raise ValueError('Replay or nonce gap')
        verify_signature(body['sender'], tx['signature'], canonical(['BKILLINGS', VERSION, 'transaction', body]))
        result['nonces'][body['sender']] = body['nonce']
        event = body['event_type']
        result['counters'][event] = result['counters'].get(event, 0)+1
        result['event_root'] = digest('event-chain', [result['event_root'], digest('signed-transaction', tx)])
    return result


def propose(spec, state, height, parent, previous_time, txs, timestamp):
    integer(height, 1); integer(timestamp); integer(previous_time); hexvalue(parent)
    if timestamp < previous_time: raise ValueError('Timestamp regression')
    new_state = transition(state, txs, spec, timestamp)
    return {'version': VERSION, 'spec': spec_id(spec), 'height': height,
            'parent': parent, 'timestamp': timestamp, 'transactions': deepcopy(txs),
            'state_root': digest('state', new_state)}


def validate_proposal(block, spec, state, height, parent, previous_time, now=None):
    exact(block, 'version spec height parent timestamp transactions state_root')
    canonical(block)
    integer(block['height'], 1); integer(block['timestamp'])
    if type(block['version']) is not int or block['version'] != VERSION or block['spec'] != spec_id(spec): raise ValueError('Block domain')
    if block['height'] != height or block['parent'] != parent: raise ValueError('Block linkage')
    if block['timestamp'] < previous_time: raise ValueError('Timestamp regression')
    if now is not None:
        integer(now)
        if block['timestamp'] > now + DRIFT: raise ValueError('Future live proposal')
    state = transition(state, block['transactions'], spec, block['timestamp'])
    if block['state_root'] != digest('state', state): raise ValueError('State root mismatch')
    return state


def vote_message(spec, block):
    return canonical(['BKILLINGS', VERSION, 'finality-vote', spec_id(spec), spec['epoch'], block['height'], digest('block', block)])


def verify_certificate(spec, block, votes):
    if type(votes) is not list or len(votes) > len(spec['validators']): raise ValueError('Invalid certificate')
    seen = set()
    for vote in votes:
        exact(vote, 'validator signature')
        key = vote['validator']
        if type(key) is not str or key not in spec['validators'] or key in seen: raise ValueError('Duplicate or unknown validator')
        verify_signature(key, vote['signature'], vote_message(spec, block))
        seen.add(key)
    if len(seen) < len(spec['validators'])-spec['faults']: raise ValueError('Insufficient quorum')
    return True
