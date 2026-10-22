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


def delete_user(email: str) -> None:
    _table().delete_item(Key={"email": email})


def list_users() -> list[dict]:
    table = _table()
    resp = table.scan()
    items = list(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items


def update_user(email: str, changes: dict, remove: tuple[str, ...] = ()) -> dict | None:
    """Asigna `changes` y quita `remove`. Devuelve el usuario o None si no existe."""
    names = {f"#{k}": k for k in (*changes, *remove)}
    parts = []
    if changes:
        parts.append("SET " + ", ".join(f"#{k} = :{k}" for k in changes))
    if remove:
        parts.append("REMOVE " + ", ".join(f"#{k}" for k in remove))
    kwargs = {}
    if changes:
        kwargs["ExpressionAttributeValues"] = {f":{k}": v for k, v in changes.items()}
    try:
        resp = _table().update_item(
            Key={"email": email},
            UpdateExpression=" ".join(parts),
            ConditionExpression="attribute_exists(email)",
            ExpressionAttributeNames=names,
            ReturnValues="ALL_NEW",
            **kwargs,
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return resp["Attributes"]
