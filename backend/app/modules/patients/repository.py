"""Acceso a la tabla patients de DynamoDB."""

from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.dynamo import get_table


def _table():
    return get_table(get_settings().table_patients)


def get_patient(patient_code: str) -> dict | None:
    return _table().get_item(Key={"patient_code": patient_code}).get("Item")


def create_patient(item: dict) -> bool:
    """Devuelve False si el código ya existe."""
    try:
        _table().put_item(Item=item, ConditionExpression="attribute_not_exists(patient_code)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def list_patients() -> list[dict]:
    table = _table()
    resp = table.scan()
    items = list(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items


def set_name(patient_code: str, name: str) -> dict | None:
    """Devuelve el paciente actualizado o None si no existe."""
    try:
        resp = _table().update_item(
            Key={"patient_code": patient_code},
            UpdateExpression="SET #n = :n",
            ConditionExpression="attribute_exists(patient_code)",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":n": name},
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return resp["Attributes"]


def _update_if(patient_code: str, field: str, ts: str, op: str) -> None:
    """Actualiza `field` solo si la condición (`field op ts`) se cumple."""
    try:
        _table().update_item(
            Key={"patient_code": patient_code},
            UpdateExpression=f"SET {field} = :ts",
            ConditionExpression=f"{field} {op} :ts",
            ExpressionAttributeValues={":ts": ts},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise


def touch_patient(patient_code: str, ts: str, device_id: str) -> None:
    """Crea al paciente si no existe, registra el dispositivo y mantiene first/last_seen.

    Los lotes pueden llegar desordenados, por eso se comparan los ts (ISO-8601 UTC).
    """
    _table().update_item(
        Key={"patient_code": patient_code},
        UpdateExpression=(
            "SET first_seen = if_not_exists(first_seen, :ts), "
            "last_seen = if_not_exists(last_seen, :ts) "
            "ADD device_ids :d"
        ),
        ExpressionAttributeValues={":ts": ts, ":d": {device_id}},
    )
    _update_if(patient_code, "last_seen", ts, "<")
    _update_if(patient_code, "first_seen", ts, ">")
