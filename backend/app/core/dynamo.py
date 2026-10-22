"""Cliente de DynamoDB compartido por los repositorios."""

import os
from functools import lru_cache

import boto3


@lru_cache
def get_resource():
    # DYNAMODB_ENDPOINT solo se define en el perfil local; en AWS queda vacío.
    return boto3.resource("dynamodb", endpoint_url=os.environ.get("DYNAMODB_ENDPOINT") or None)


def get_table(name: str):
    return get_resource().Table(name)


# Ítem reservado que guarda el último número asignado en una tabla (códigos automáticos).
# El carácter "#" no es válido en los identificadores reales, así que no puede chocar con ellos.
COUNTER_KEY = "#counter"


def next_number(table, key_name: str) -> int:
    """Incrementa de forma atómica el contador de la tabla y devuelve el nuevo valor."""
    resp = table.update_item(
        Key={key_name: COUNTER_KEY},
        UpdateExpression="ADD #v :one",
        ExpressionAttributeNames={"#v": "value"},
        ExpressionAttributeValues={":one": 1},
        ReturnValues="UPDATED_NEW",
    )
    return int(resp["Attributes"]["value"])
