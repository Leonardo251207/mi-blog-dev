# Despliegue de los servicios del ecosistema

Esta guía documenta cómo se desplegaron y conectaron los dos servicios descargados
del repositorio del profesor:

- `metrics-navigation-main` → **Metrics Collector & Retriever**.
- `static-sites-generator-main` → **Static Sites Generator**.

No se reescribieron los servicios: se ejecutan desde sus propios repositorios y se
conectaron con el CMS y el blog.

## Puertos

| Servicio | Puerto | URL |
|---|---:|---|
| CMS DevBlog | 8080 | <http://127.0.0.1:8080> |
| Metrics Collector & Retriever | 8000 | <http://127.0.0.1:8000> |
| Static Sites Generator | 8001 | <http://127.0.0.1:8001> |
| Blog estático | 5500 | <http://127.0.0.1:5500> |

El CMS se movió de 8000 a 8080 para respetar la arquitectura del ecosistema:
Métricas en 8000, Generador en 8001 y CMS en 8080.

Para levantar los cuatro servicios de una vez, desde la raíz del proyecto:

```powershell
.\start-all.ps1
```

Cada servicio se abre en su propia ventana de PowerShell. Para detenerlos, cierra
cada ventana o pulsa `Ctrl+C` dentro de ella.

---

## 1. Metrics Collector & Retriever (8000)

### Instalación

```powershell
cd pendiente\metrics-navigation-main\metrics-navigation-main
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

### Configuración local

Se creó `.env` con:

```env
APP_ENV=local
APP_MODE=minimal
APP_PORT=8000
STORAGE=memory
MONGO_URI=
MONGO_DB=metrics
ADMIN_API_KEY=dev-admin-key
IP_HASH_SALT=dev-salt-change-me
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
BOOTSTRAP_FILE=config/bootstrap.devblog.yaml
BOOTSTRAP_ON_START=true
DEV_BEACON_KEY=pk_live_dev_00000000000000000000000000000000
BEACON_RATE_LIMIT_PER_MINUTE=600
```

`STORAGE=memory` evita instalar MongoDB. Los eventos viven mientras el proceso
esté arriba; para persistencia real se usa `STORAGE=mongo` y `MONGO_URI`.

El archivo `config/bootstrap.devblog.yaml` crea dos sitios:

- `demo`: el sitio de laboratorio original.
- `devblog`: el sitio real del blog, con dominios `localhost:5500` y
  `127.0.0.1:5500`, y un canal beacon con la clave pública
  `pk_live_devblog_0000000000000000000000000000`.

### Arranque

```powershell
cd pendiente\metrics-navigation-main\metrics-navigation-main
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Verificación

- Salud: <http://127.0.0.1:8000/health>
- GraphiQL: <http://127.0.0.1:8000/v1/query>
- Demo del beacon: <http://127.0.0.1:8000/v1/demo>

> El endpoint REST `/api/v1/documents/{id}/metrics` del repo de métricas sigue
> devolviendo valores de ejemplo. Para tráfico real se usa GraphQL
> (`/v1/query`), que lee los eventos del beacon.

Consulta GraphQL de ejemplo:

```graphql
{
  sitios {
    slug
    nombre
    estado
  }
}
```

Consulta de tráfico del blog:

```graphql
{
  trafico(
    sitioSlug: "devblog"
    desde: "2026-11-04T00:00:00Z"
    hasta: "2026-11-06T00:00:00Z"
    grano: DIA
  ) {
    pageviews
    sesiones
    visitantesUnicosEstimados
    porRuta { clave valor }
    porHost { clave valor }
  }
}
```

### Integración con el blog

`dev-blog/metrics.js` inyecta el beacon cuando `METRICS_ENABLED` está activo en
`dev-blog/api-config.js`:

```js
METRICS_ENABLED: true,
METRICS_BASE_URL: "http://127.0.0.1:8000",
METRICS_KEY: "pk_live_devblog_0000000000000000000000000000",
METRICS_SITE: "devblog",
```

El beacon se carga en la portada, el artículo dinámico y las tres páginas de
artículo existentes.

### Correcciones locales aplicadas al repo del profesor

1. `app/shared/ids.py` → `detectar_entorno` ahora reconoce loopback con puerto
   (`127.0.0.1:5500`), no solo `localhost:5500`.
2. `app/main.py` → CORS con `allow_credentials=True` para que
   `navigator.sendBeacon` no sea bloqueado por el navegador.

---

## 2. Static Sites Generator (8001)

### Instalación

```powershell
cd pendiente\static-sites-generator-main\static-sites-generator-main
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

### Arranque

```powershell
cd pendiente\static-sites-generator-main\static-sites-generator-main
.venv\Scripts\activate
uvicorn src.main:app --host 127.0.0.1 --port 8001
```

### Verificación

- Swagger: <http://127.0.0.1:8001/docs>
- Salud: <http://127.0.0.1:8001/health>

### Integración con el CMS

La consola del CMS tiene el botón **Generar HTML estático**. Toma el título, el
slug, las etiquetas y el Markdown del borrador/publicación, los convierte en
bloques (`HEADING`, `PARAGRAPH`, `CODE`, `QUOTE`, `IMAGE`) y llama a:

```http
POST http://127.0.0.1:8001/api/v1/pages
```

El resultado incluye `page_id`, `status`, `engine`, `checksum_sha256` y
`output_url`. La consola muestra el checksum y un enlace para abrir el HTML.

Para generar todos los artículos publicados de una vez:

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\activate
python scripts\generate_static.py
```

Los artefactos se guardan en:

```text
dev-blog\generated\{slug}.html
```

También quedan servidos por el generador en
`/api/v1/pages/{page_id}/content`.

---

## 3. CMS DevBlog (8080)

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

- Documentación: <http://127.0.0.1:8080/docs>
- Salud: <http://127.0.0.1:8080/health>

El frontend apunta a `http://127.0.0.1:8080/api/v1` en
`dev-blog/api-config.js`.

---

## 4. Blog estático (5500)

```powershell
cd dev-blog
python -m http.server 5500
```

- Blog: <http://127.0.0.1:5500/>
- Consola CMS: <http://127.0.0.1:5500/admin.html>
  - Token: `console-dev-token`

---

## 5. Flujo completo

```text
Navegador (blog 5500)
   ├── GET  :8080/api/v1/posts          → lista publicaciones del CMS
   ├── GET  :8080/api/v1/posts/slug/... → artículo completo
   ├── POST :8080/api/v1/posts/{id}/views → vista propia del CMS
   └── beacon :8000/v1/collect          → pageview/engagement para métricas

Consola CMS (5500/admin.html)
   ├── CRUD :8080/api/v1/drafts
   ├── POST :8080/api/v1/drafts/{id}/publish
   └── POST :8001/api/v1/pages          → HTML estático del artículo
```

## 6. Pruebas

```powershell
# CMS
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\python.exe -m pytest -q
# 43 passed

# Métricas
cd pendiente\metrics-navigation-main\metrics-navigation-main
.venv\Scripts\python.exe -m pytest tests -q
# 13 passed

# Generador estático
cd pendiente\static-sites-generator-main\static-sites-generator-main
.venv\Scripts\python.exe -m unittest tests/test_api.py -v
# 4 passed
```

## 7. Notas

- El generador estático no tiene autenticación y su CORS es abierto; es para
  local. En producción debe ir detrás de un proxy/autenticación.
- El colector de métricas en `STORAGE=memory` pierde eventos al reiniciar.
- Los artefactos del generador son HTML simple con el contenido en `<pre>`; la
  página dinámica del blog sigue siendo la versión con el diseño del DevBlog_.
- No se usó Docker porque no está instalado en la máquina. Los `Dockerfile` y
  `docker-compose.yml` de los repos quedan disponibles para un despliegue futuro.
