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
