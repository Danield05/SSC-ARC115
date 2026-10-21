"""Controlador HTTP del módulo measurements."""

from fastapi import APIRouter

router = APIRouter(prefix="/measurements", tags=["measurements"])

# TODO: POST /measurements (x-api-key, validación, escritura condicional).
