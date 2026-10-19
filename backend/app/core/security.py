"""Seguridad: hash de la clave del dispositivo y comparación en tiempo constante."""

import hashlib
import hmac


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(api_key), expected_hash)
