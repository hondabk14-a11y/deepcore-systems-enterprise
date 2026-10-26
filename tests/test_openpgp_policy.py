"""Adapter policy/I/O tests with a simulated GnuPG process, not crypto evidence."""
import subprocess
from pathlib import Path

import pytest

from SECURITY.openpgp import OpenPGP, OpenPGPError

PIN = 'A' * 40
SUB = 'B' * 40
OTHER = 'C' * 40


def status(*lines):
    return ''.join('[GNUPG:] ' + line + '\n' for line in lines)


def listing(selected=PIN, validity='u'):
    def row(tag, valid='', fpr=''):
        fields = [''] * 12
        fields[0], fields[1], fields[9] = tag, valid, fpr
        return ':'.join(fields) + '\n'
    out = row('pub', 'u') + row('fpr', fpr=PIN)
    if selected != PIN:
        out += row('sub', validity) + row('fpr', fpr=selected)
    elif validity != 'u':
        out = row('pub', validity) + row('fpr', fpr=PIN)
    return out


def simulate(monkeypatch, client, output_status, *, returncode=0, selected=PIN,
             validity='u', before_return=None):
    monkeypatch.setattr(client, 'require_key', lambda **kwargs: None)
    def run(*args):
        if '--list-keys' in args:
            return subprocess.CompletedProcess(args, 0, listing(selected, validity), '')
        target = Path(args[args.index('--output') + 1])
        target.write_bytes(b'plaintext emitted before final status')
        if before_return:
            before_return()
        return subprocess.CompletedProcess(args, returncode, output_status, '')
    monkeypatch.setattr(client, '_run', run)


@pytest.fixture
def artifact(tmp_path):
    source = tmp_path / 'input.pgp'
    source.write_bytes(b'simulated ciphertext')
    return source, tmp_path / 'output.txt'


@pytest.mark.parametrize('selected', [PIN, SUB])
def test_only_validated_plaintext_is_published(monkeypatch, artifact, selected):
    source, dest = artifact
    client = OpenPGP(PIN)
    simulate(monkeypatch, client, status(f'DECRYPTION_KEY {selected} {PIN} u',
             'DECRYPTION_INFO 2 9 0', 'DECRYPTION_OKAY', 'GOODMDC'), selected=selected)
    assert client.decrypt(source, dest) == dest
    assert dest.read_bytes() == b'plaintext emitted before final status'
    assert dest.stat().st_mode & 0o777 == 0o600
    assert not list(dest.parent.glob('.openpgp-*'))


@pytest.mark.parametrize('records', [
    [f'DECRYPTION_KEY {OTHER} {OTHER} u', 'DECRYPTION_OKAY', 'GOODMDC'],
    ['DECRYPTION_OKAY', 'GOODMDC'],
    ['DECRYPTION_KEY', 'DECRYPTION_OKAY', 'GOODMDC'],
    [f'DECRYPTION_KEY {PIN} {PIN} u'] * 2 + ['DECRYPTION_OKAY', 'GOODMDC'],
    [f'DECRYPTION_KEY {PIN} {PIN} u', 'DECRYPTION_OKAY'],
    [f'DECRYPTION_KEY {PIN} {PIN} u', 'GOODMDC'],
    [f'DECRYPTION_KEY {PIN} {PIN} u', 'DECRYPTION_OKAY', 'GOODMDC', 'BADMDC'],
    [f'DECRYPTION_KEY {PIN} {PIN} u', 'DECRYPTION_OKAY', 'GOODMDC', 'DECRYPTION_FAILED'],
])
def test_untrusted_plaintext_never_published(monkeypatch, artifact, records):
    source, dest = artifact
    client = OpenPGP(PIN)
    simulate(monkeypatch, client, status(*records))
    with pytest.raises(OpenPGPError):
        client.decrypt(source, dest)
    assert not dest.exists()
    assert not list(dest.parent.glob('.openpgp-*'))


@pytest.mark.parametrize('operation', ['decrypt', 'encrypt', 'sign'])
def test_failed_process_removes_partial_output(monkeypatch, artifact, operation):
    source, dest = artifact
    client = OpenPGP(PIN)
    simulate(monkeypatch, client, '', returncode=2)
    with pytest.raises(OpenPGPError):
        getattr(client, operation)(source, dest)
    assert not dest.exists()
    assert not list(dest.parent.glob('.openpgp-*'))


@pytest.mark.parametrize('validity', ['e', 'r', 'd', 'i'])
def test_invalid_decryption_subkey_rejected(monkeypatch, artifact, validity):
    source, dest = artifact
    client = OpenPGP(PIN)
    simulate(monkeypatch, client, status(f'DECRYPTION_KEY {SUB} {PIN} u',
             'DECRYPTION_OKAY', 'GOODMDC'), selected=SUB, validity=validity)
    with pytest.raises(OpenPGPError):
        client.decrypt(source, dest)
    assert not dest.exists()


@pytest.mark.parametrize('symlink', [False, True])
def test_publication_race_cannot_overwrite(monkeypatch, artifact, symlink):
    source, dest = artifact
    client = OpenPGP(PIN)
    victim = dest.parent / 'keep.txt'
    victim.write_text('keep')
    def concurrent_writer():
        if symlink:
            dest.symlink_to(victim)
        else:
            dest.write_text('keep')
    simulate(monkeypatch, client, status(f'DECRYPTION_KEY {PIN} {PIN} u',
             'DECRYPTION_OKAY', 'GOODMDC'), before_return=concurrent_writer)
    with pytest.raises(OpenPGPError):
        client.decrypt(source, dest)
    assert dest.read_text() == 'keep'
    assert victim.read_text() == 'keep'
    assert not list(dest.parent.glob('.openpgp-*'))


@pytest.mark.parametrize('validity', ['e', 'r', 'd', 'i'])
@pytest.mark.parametrize('secret', [False, True])
def test_invalid_primary_key_rejected(monkeypatch, validity, secret):
    client = OpenPGP(PIN)
    text = listing(validity=validity).replace('pub:', 'sec:') if secret else listing(validity=validity)
    monkeypatch.setattr(client, '_run', lambda *a: subprocess.CompletedProcess(a, 0, text, ''))
    with pytest.raises(OpenPGPError):
        client.require_key(secret=secret)


@pytest.mark.parametrize('bad', ['EXPKEYSIG', 'REVKEYSIG', 'EXPSIG'])
def test_bad_signature_status_overrides_validsig(monkeypatch, artifact, bad):
    source, sig = artifact
    sig.write_text('signature')
    client = OpenPGP(PIN)
    monkeypatch.setattr(client, 'require_key', lambda: None)
    out = status(f'VALIDSIG {SUB} 2026-01-01 1 0 4 0 1 10 00 {PIN}', bad + ' key uid')
    monkeypatch.setattr(client, '_run', lambda *a: subprocess.CompletedProcess(a, 0, out, ''))
    assert client.verify(source, sig) is False
