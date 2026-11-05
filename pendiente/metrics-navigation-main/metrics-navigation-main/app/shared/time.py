"""Rangos temporales, zonas horarias y cubos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.shared.enums import Grano
from app.shared.errors import DomainError

UTC = timezone.utc


def asegurar_utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


def zona(valor: str) -> ZoneInfo:
    try:
        return ZoneInfo(valor)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def validar_rango(
    desde: datetime,
    hasta: datetime,
    grano: Grano = Grano.DIA,
    *,
    max_dias: int = 366,
) -> tuple[datetime, datetime]:
    desde = asegurar_utc(desde)
    hasta = asegurar_utc(hasta)
    if desde >= hasta:
        raise DomainError(
            "RANGO_INVALIDO",
            "`desde` debe ser anterior a `hasta`.",
            status_code=422,
        )
    if hasta - desde > timedelta(days=max_dias):
        raise DomainError(
            "RANGO_INVALIDO",
            f"El rango máximo es de {max_dias} días.",
            status_code=422,
        )
    if grano == Grano.HORA and hasta - desde > timedelta(days=7):
        raise DomainError(
            "RANGO_INVALIDO",
            "El grano HORA solo está permitido para rangos de 7 días o menos.",
            status_code=422,
        )
    return desde, hasta


def inicio_cubo(valor: datetime, grano: Grano, zona_horaria: str = "UTC") -> datetime:
    """Devuelve el inicio del cubo en UTC, calculado en la zona de la propiedad."""
    local = asegurar_utc(valor).astimezone(zona(zona_horaria))
    if grano == Grano.HORA:
        local = local.replace(minute=0, second=0, microsecond=0)
    else:
        local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return local.astimezone(UTC)


def cubos(desde: datetime, hasta: datetime, grano: Grano, zona_horaria: str = "UTC") -> list[datetime]:
    """Lista de cubos entre dos fechas, incluyendo el primero y excluyendo el último."""
    actual = inicio_cubo(desde, grano, zona_horaria)
    fin = asegurar_utc(hasta)
    paso = timedelta(hours=1) if grano == Grano.HORA else timedelta(days=1)
    salida: list[datetime] = []
    while actual < fin:
        salida.append(actual)
        actual = actual + paso
    return salida
