"""Acceso a la tabla measurements de DynamoDB."""

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
