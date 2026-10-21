"""Acceso a la tabla users de DynamoDB."""

from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.dynamo import get_table


def _table():
    return get_table(get_settings().table_users)


def get_user(email: str) -> dict | None:
    return _table().get_item(Key={"email": email}).get("Item")


def create_user(item: dict) -> bool:
    """Devuelve False si el correo ya existe."""
    try:
        _table().put_item(Item=item, ConditionExpression="attribute_not_exists(email)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def list_users() -> list[dict]:
    table = _table()
    resp = table.scan()
    items = list(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items


def set_active(email: str, active: bool) -> dict | None:
    """Devuelve el usuario actualizado o None si no existe."""
    try:
        resp = _table().update_item(
            Key={"email": email},
            UpdateExpression="SET active = :a",
            ConditionExpression="attribute_exists(email)",
            ExpressionAttributeValues={":a": active},
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return resp["Attributes"]
