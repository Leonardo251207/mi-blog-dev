import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.bootstrap.container import build_container
from app.bootstrap.settings import Settings
from app.main import create_app
from tests.helpers import TEST_ADMIN, TEST_KEY


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        storage="memory",
        mongo_uri="",
        admin_api_key=TEST_ADMIN,
        ip_hash_salt="test-salt",
        dev_beacon_key=TEST_KEY,
        bootstrap_on_start=False,
        cors_origins="http://testserver",
    )


@pytest_asyncio.fixture
async def container(settings: Settings):
    actual = await build_container(settings)
    yield actual
    await actual.close()


@pytest_asyncio.fixture
async def app(settings: Settings, container):
    return create_app(settings=settings, container=container)


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as actual:
        yield actual


@pytest_asyncio.fixture
async def sitio(container):
    from app.shared.enums import Entorno, ModoOrigen, TipoCanal, TipoDominio, TipoSitio

    propiedad = await container.properties_service.crear_sitio(
        slug="demo",
        nombre="Demo",
        tipo=TipoSitio.LABORATORIO,
    )
    await container.properties_service.registrar_dominio(
        propiedad=propiedad,
        host="testserver",
        tipo=TipoDominio.TEMPORAL,
        entorno=Entorno.PRODUCTION,
        es_canonico=True,
    )
    canal, _ = await container.properties_service.crear_canal(
        propiedad=propiedad,
        tipo=TipoCanal.BEACON,
        modo_origen=ModoOrigen.EXACTO,
        origenes=["http://testserver"],
        entornos=[Entorno.PRODUCTION],
        clave_publica=TEST_KEY,
    )
    return propiedad, canal
