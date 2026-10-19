import secrets

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_api_key,
    hash_password,
    verify_api_key,
    verify_password,
)


def test_verify_api_key():
    key = secrets.token_urlsafe(16)
    h = hash_api_key(key)
    assert verify_api_key(key, h)
    assert not verify_api_key("otra", h)


def test_password_hash_roundtrip():
    password = secrets.token_urlsafe(12)
    stored = hash_password(password)
    assert stored != password
    assert verify_password(password, stored)
    assert not verify_password("otra-clave", stored)
    assert not verify_password(password, "formato-invalido")


def test_token_roundtrip_and_tampering():
    secret = secrets.token_hex(32)
    token = create_access_token("a@example.com", "admin", secret)
    assert decode_access_token(token, secret)["role"] == "admin"
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token, secrets.token_hex(32))
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(create_access_token("a@example.com", "admin", secret, -1), secret)
