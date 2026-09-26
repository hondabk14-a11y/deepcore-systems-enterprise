"""Encrypted local Ed25519 key files; passphrases never saved by this module."""
import os
import stat
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from protocol import public


def create_key(path, passphrase):
    if type(passphrase) is not bytes or len(passphrase) < 16: raise ValueError('Passphrase must be at least 16 bytes')
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.BestAvailableEncryption(passphrase))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(pem); stream.flush(); os.fsync(stream.fileno())
    directory = os.open(str(Path(path).parent), os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(directory)
    finally: os.close(directory)
    return public(key)


def load_key(path, passphrase):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
            raise ValueError('Key file ownership or permissions unsafe')
        raw = stream.read(16385)
        if len(raw) > 16384 or not raw.startswith(b'-----BEGIN ENCRYPTED PRIVATE KEY-----'):
            raise ValueError('Expected bounded encrypted PEM')
        key = serialization.load_pem_private_key(raw, passphrase)
        if not isinstance(key, Ed25519PrivateKey): raise ValueError('Wrong key algorithm')
        return key
