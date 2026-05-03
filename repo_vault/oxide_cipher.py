import gzip
import os

from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA1
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad


def _derive_block_key(secret_phrase, salt_bytes):
    return PBKDF2(
        secret_phrase,
        salt_bytes,
        dkLen=16,
        count=100,
        prf=lambda password, salt: HMAC.new(password, salt, SHA1).digest(),
    )


def unwrap_payload(file_path, secret_phrase):
    with open(file_path, "rb") as file_handle:
        payload = file_handle.read()

    iv = payload[:16]
    encrypted_body = payload[16:]
    key = _derive_block_key(secret_phrase, iv)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted_body), AES.block_size)

    if decrypted[:2] == b"\x1f\x8b":
        decrypted = gzip.decompress(decrypted)

    return decrypted


def wrap_payload(raw_bytes, secret_phrase, compress=False):
    if compress:
        raw_bytes = gzip.compress(raw_bytes)

    iv = os.urandom(16)
    key = _derive_block_key(secret_phrase, iv)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_body = cipher.encrypt(pad(raw_bytes, AES.block_size))
    return iv + encrypted_body
