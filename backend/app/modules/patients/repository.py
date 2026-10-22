"""Acceso a la tabla patients de DynamoDB."""

from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.dynamo import COUNTER_KEY, get_table, next_number


def _table():
    return get_table(get_settings().table_patients)


def get_patient(patient_code: str) -> dict | None:
    if patient_code == COUNTER_KEY:
        return None
    return _table().get_item(Key={"patient_code": patient_code}).get("Item")


def next_code_number() -> int:
    return next_number(_table(), "patient_code")


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
    return [i for i in items if i["patient_code"] != COUNTER_KEY]


def update_patient(patient_code: str, changes: dict, remove: tuple[str, ...] = ()) -> dict | None:
    """Asigna `changes` y quita `remove`. Devuelve el paciente o None si no existe."""
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
            Key={"patient_code": patient_code},
            UpdateExpression=" ".join(parts),
            ConditionExpression="attribute_exists(patient_code)",
            ExpressionAttributeNames=names,
            ReturnValues="ALL_NEW",
            **kwargs,
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
