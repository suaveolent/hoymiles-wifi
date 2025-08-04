"""Crypto utils for interacting with encrypted Hoymiles DTUs."""

import struct
from hashlib import sha256

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from hoymiles_wifi import logger


def sha256_bytes(data: bytes) -> bytes:
    """Return SHA256 hash of the input data."""
    return sha256(data).digest()


def derive_aes_128_key(encRand: bytes) -> bytes:
    """Derive a 128-bit AES key by triple SHA256 hashing the encRand."""
    assert len(encRand) == 16
    digest = sha256_bytes(sha256_bytes(sha256_bytes(encRand)))
    return digest[:16]  # AES-128 key


def derive_nonce(encRand: bytes, u16_tag: int, u16_seq: int) -> bytes:
    """Derive a nonce for AES-GCM by tripple SHA256 hashing the encRand, tag, and sequence."""
    tag_bytes = struct.pack("<H", u16_tag)
    seq_bytes = struct.pack("<H", u16_seq)

    buffer = tag_bytes + seq_bytes + encRand

    assert len(buffer) == 20

    digest = sha256_bytes(sha256_bytes(sha256_bytes(buffer)))

    return digest[-12:]  # digest[20:32]


def crypt_data(
    encrypt: bool, enc_rand: bytes, u16_tag: int, u16_seq: int, input_data: bytes
) -> bytes:
    """Encrypt or decrypt data using AES-GCM with the provided parameters."""

    key = derive_aes_128_key(enc_rand)
    nonce = derive_nonce(enc_rand, u16_tag, u16_seq)
    aad = struct.pack("<HH", u16_tag, u16_seq)

    logger.debug(f"[*] CMD  : {hex(u16_tag)}")
    logger.debug(f"[*] Seq  : {hex(u16_seq)}")
    logger.debug(f"[*] Enc rand: {enc_rand.hex()} ({len(enc_rand)})")
    logger.debug(f"[*] Nonce: {nonce.hex()} ({len(nonce)})")
    logger.debug(f"[*] AAD  : {aad.hex()} ({len(aad)})")
    logger.debug(f"[*] Key  : {key.hex()} ({len(key)})")

    aesgcm = AESGCM(key)
    try:
        if encrypt:
            output_data = aesgcm.encrypt(nonce, input_data, associated_data=aad)
            logger.debug(
                f"[*] Ciphertext: {output_data.hex()} ({len(output_data)} bytes)"
            )
        else:
            output_data = aesgcm.decrypt(nonce, input_data, associated_data=aad)

            logger.debug("[*] Decryption succeeded using AES-GCM!")
            logger.debug(
                f"[*] Plaintext: {output_data.hex()} ({len(output_data)} bytes)"
            )

        return output_data
    except Exception as e:
        raise ValueError(f"[-] AES-GCM failed: {repr(e)}") from e

    return None
