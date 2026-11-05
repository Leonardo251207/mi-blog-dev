"""Enumeraciones del dominio.

Se mantienen como `str, Enum` para que Pydantic y MongoDB las serialicen como texto y
Strawberry las exponga como enums GraphQL sin una capa de traducción.
"""

from enum import Enum


class TipoSitio(str, Enum):
    PROPIA = "PROPIA"
    AJENA = "AJENA"
    LABORATORIO = "LABORATORIO"


class EstadoSitio(str, Enum):
    ACTIVO = "ACTIVO"
    PAUSADO = "PAUSADO"
    ARCHIVADO = "ARCHIVADO"


class EstadoVerificacion(str, Enum):
    PROVISIONAL = "PROVISIONAL"
    VERIFICADO = "VERIFICADO"
    RECHAZADO = "RECHAZADO"


class TipoDominio(str, Enum):
    PROPIO = "PROPIO"
    PLATAFORMA = "PLATAFORMA"
    PREVIEW = "PREVIEW"
    TEMPORAL = "TEMPORAL"


class EstadoDominio(str, Enum):
    PENDIENTE = "PENDIENTE"
    VERIFICADO = "VERIFICADO"
    RETIRADO = "RETIRADO"


class Entorno(str, Enum):
    PRODUCTION = "production"
    PREVIEW = "preview"
    LOCAL = "local"


class TipoCanal(str, Enum):
    BEACON = "BEACON"
    EDGE = "EDGE"
    API_EXTERNA = "API_EXTERNA"
    SINTETICO = "SINTETICO"
    IMPORTACION = "IMPORTACION"


class EstadoCanal(str, Enum):
    ACTIVO = "ACTIVO"
    DEGRADADO = "DEGRADADO"
    INACTIVO = "INACTIVO"


class ModoOrigen(str, Enum):
    EXACTO = "EXACTO"
    PATRON = "PATRON"
    ABIERTO_CON_CUOTA = "ABIERTO_CON_CUOTA"


class ModoProvision(str, Enum):
    REGISTRADO = "REGISTRADO"
    AUTO = "AUTO"


class TipoEvento(str, Enum):
    PAGEVIEW = "PAGEVIEW"
    ENGAGEMENT = "ENGAGEMENT"
    SCROLL = "SCROLL"
    OUTBOUND_CLICK = "OUTBOUND_CLICK"
    DOWNLOAD = "DOWNLOAD"
    WEB_VITAL = "WEB_VITAL"


class Grano(str, Enum):
    HORA = "HORA"
    DIA = "DIA"


class Completitud(str, Enum):
    COMPLETA = "COMPLETA"
    PARCIAL = "PARCIAL"
    OBSOLETA = "OBSOLETA"
    ESTIMADA = "ESTIMADA"


class EstadoIntegracion(str, Enum):
    PENDIENTE = "PENDIENTE"
    ACTIVA = "ACTIVA"
    DEGRADADA = "DEGRADADA"
    ERROR = "ERROR"
    DESHABILITADA = "DESHABILITADA"


class TipoIntegracion(str, Enum):
    GA4 = "GA4"
    SEARCH_CONSOLE = "SEARCH_CONSOLE"
    ADSENSE = "ADSENSE"
    AD_MANAGER = "AD_MANAGER"
