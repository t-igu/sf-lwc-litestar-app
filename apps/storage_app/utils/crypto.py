# storage_server/app/security/crypto.py

from __future__ import annotations
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from apps.const import BASE_DIR, AES_KEY

# ---------------------------------------------------------
# AES256-GCM 初期化
# ---------------------------------------------------------
import base64

def get_aesgcm() -> AESGCM:
    if not AES_KEY:
        raise RuntimeError("AES256_KEY is not set in environment variables")

    try:
        key_bytes = base64.b64decode(AES_KEY)
    except Exception:
        raise RuntimeError("AES256_KEY must be valid Base64")

    if len(key_bytes) != 32:
        raise RuntimeError("AES256_KEY must decode to 32 bytes (256bit)")

    return AESGCM(key_bytes)


# ---------------------------------------------------------
# 暗号化（AES256-GCM）
# ---------------------------------------------------------
def encrypt_path(path: Path) -> str:
    aes = get_aesgcm()

    # 96bit nonce（推奨）
    nonce = os.urandom(12)

    ciphertext = aes.encrypt(
        nonce,
        str(path).encode("utf-8"),
        associated_data=None,
    )

    # nonce + ciphertext を Base64 で返す
    return (nonce + ciphertext).hex()


# ---------------------------------------------------------
# 復号化（AES256-GCM）
# ---------------------------------------------------------
def decrypt_path(enc_hex: str) -> str:
    aes = get_aesgcm()

    raw = bytes.fromhex(enc_hex)

    nonce = raw[:12]
    ciphertext = raw[12:]

    print(raw)

    plaintext = aes.decrypt(
        nonce,
        ciphertext,
        associated_data=None,
    )

    return plaintext.decode("utf-8")


# ---------------------------------------------------------
# Path Traversal 防止
# ---------------------------------------------------------
def validate_path(path: Path) -> Path:
    resolved = path.resolve()

    if not str(resolved).startswith(str(BASE_DIR)):
        raise ValueError(f"Path traversal detected: {resolved}")

    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    return resolved
