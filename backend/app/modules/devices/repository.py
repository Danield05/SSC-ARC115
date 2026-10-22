"""Acceso a la tabla devices de DynamoDB."""

from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.dynamo import COUNTER_KEY, get_table, next_number


def _table():
    return get_table(get_settings().table_devices)


def get_device(device_id: str) -> dict | None:
    if device_id == COUNTER_KEY:
        return None
    return _table().get_item(Key={"device_id": device_id}).get("Item")


def next_id_number() -> int:
    return next_number(_table(), "device_id")


def create_device(item: dict) -> bool:
    """Devuelve False si el device_id ya existe."""
    try:
        _table().put_item(Item=item, ConditionExpression="attribute_not_exists(device_id)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def list_devices() -> list[dict]:
    table = _table()
    resp = table.scan()
    items = list(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return [i for i in items if i["device_id"] != COUNTER_KEY]


def update_device(device_id: str, changes: dict) -> dict | None:
    """Actualiza campos sueltos. Devuelve el dispositivo o None si no existe."""
    names = {f"#{k}": k for k in changes}
    values = {f":{k}": v for k, v in changes.items()}
    expr = "SET " + ", ".join(f"#{k} = :{k}" for k in changes)
    try:
        resp = _table().update_item(
            Key={"device_id": device_id},
            UpdateExpression=expr,
            ConditionExpression="attribute_exists(device_id)",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return resp["Attributes"]
