"""Traducción entre modelos Pydantic y documentos MongoDB."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _convertir(valor: Any) -> Any:
    if isinstance(valor, Enum):
        return valor.value
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, dict):
        return {clave: _convertir(item) for clave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_convertir(item) for item in valor]
    return valor


def to_doc(modelo: BaseModel) -> dict[str, Any]:
    datos = _convertir(modelo.model_dump())
    if "id" in datos:
        datos["_id"] = datos.pop("id")
    elif "id_evento" in datos:
        datos["_id"] = datos["id_evento"]
    return datos


def from_doc(documento: dict[str, Any], tipo: type[T]) -> T:
    datos = dict(documento)
    if "_id" in datos:
        identificador = datos.pop("_id")
        if "id" in tipo.model_fields:
            datos["id"] = identificador
        elif "id_evento" in tipo.model_fields:
            datos["id_evento"] = identificador
    return tipo.model_validate(datos)
