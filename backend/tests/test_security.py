from app.core.security import hash_api_key, verify_api_key


def test_verify_api_key():
    h = hash_api_key("clave-de-prueba")
    assert verify_api_key("clave-de-prueba", h)
    assert not verify_api_key("otra", h)
