import secrets

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.core.config import get_settings
from app.core.dynamo import get_resource
from app.main import app
from app.modules.auth import service as auth_service


def _clear_caches():
    get_settings.cache_clear()
    get_resource.cache_clear()


@pytest.fixture(autouse=True)
def aws(monkeypatch):
    """Base DynamoDB en memoria (moto) con las tablas que usan los tests."""
    monkeypatch.delenv("DYNAMODB_ENDPOINT", raising=False)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("JWT_SECRET", secrets.token_hex(32))
    _clear_caches()
    with mock_aws():
        db = boto3.resource("dynamodb")
        for name, key in (
            ("devices", "device_id"),
            ("users", "email"),
            ("patients", "patient_code"),
        ):
            db.create_table(
                TableName=name,
                BillingMode="PAY_PER_REQUEST",
                AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"}],
                KeySchema=[{"AttributeName": key, "KeyType": "HASH"}],
            )
        db.create_table(
            TableName="measurements",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "patient_code", "AttributeType": "S"},
                {"AttributeName": "ts", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "patient_code", "KeyType": "HASH"},
                {"AttributeName": "ts", "KeyType": "RANGE"},
            ],
        )
        yield
    _clear_caches()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_user(client):
    """Crea un usuario y devuelve su contraseña y las cabeceras con su token."""

    def _make(email: str, role: str):
        password = secrets.token_urlsafe(12)
        auth_service.create_user(email, password, role)
        token = client.post("/auth/login", json={"email": email, "password": password}).json()[
            "access_token"
        ]
        return password, {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def admin(make_user):
    return make_user("admin@example.com", "admin")[1]
