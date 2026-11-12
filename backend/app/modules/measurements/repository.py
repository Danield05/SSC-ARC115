"""Acceso a la tabla measurements de DynamoDB."""

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.dynamo import get_table


def _table():
    return get_table(get_settings().table_measurements)


def put_measurement(item: dict) -> bool:
    """Escribe solo si no existe (patient_code, ts). Devuelve False si es un reenvío."""
    try:
        _table().put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(patient_code) AND attribute_not_exists(ts)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def get_measurement(patient_code: str, ts: str) -> dict | None:
    return _table().get_item(Key={"patient_code": patient_code, "ts": ts}).get("Item")


def set_review(patient_code: str, ts: str, review: dict) -> bool:
    """Guarda la revisión (reemplaza la anterior). False si la medición ya no existe."""
    try:
        _table().update_item(
            Key={"patient_code": patient_code, "ts": ts},
            UpdateExpression="SET #r = :r",
            ExpressionAttributeNames={"#r": "review"},
            ExpressionAttributeValues={":r": review},
            ConditionExpression="attribute_exists(patient_code)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def list_measurements(patient_code: str, start: str, end: str, limit: int) -> list[dict]:
    """Las `limit` mediciones más recientes del paciente entre `start` y `end`, de la más
    antigua a la más nueva."""
    table = _table()
    kwargs = {
        "KeyConditionExpression": Key("patient_code").eq(patient_code)
        & Key("ts").between(start, end),
        "ScanIndexForward": False,
        "Limit": limit,
    }
    items: list[dict] = []
    resp = table.query(**kwargs)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp and len(items) < limit:
        resp = table.query(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return list(reversed(items[:limit]))
