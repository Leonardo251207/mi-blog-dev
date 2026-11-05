# DevBlog CMS API (v1.2)

Implementación en **FastAPI** de la *Especificación de Arquitectura y Contrato de
Interfaz v1.2* (API-First). Persistencia real en **SQLite** y cliente web incluido
para conectar el blog.

## Documentación de la entrega

El contrato original se conserva intacto. La versión documentada añade un
**Anexo D** con la implementación de referencia, la conexión con el blog y las
decisiones operativas:

- [`Especificacion_API_CMS_DevBlog_v1.2_implementacion.docx`](../../Especificacion_API_CMS_DevBlog_v1.2_implementacion.docx)
- [`Especificacion_API_CMS_DevBlog_v1.2_implementacion.pdf`](../../Especificacion_API_CMS_DevBlog_v1.2_implementacion.pdf)

## Qué incluye esta versión

- Los 12 endpoints del contrato (`/drafts` y `/posts`).
- Persistencia en SQLite (los artículos sobreviven al reinicio).
- Configuración por entorno o `.env` para reutilizar la API en otro proyecto.
- CORS para que el blog estático pueda consumir la API desde otro origen.
- Cursor de paginación **firmado** con HMAC: un cursor alterado responde 422.
- Errores 500 con el mismo formato `{"error": {...}}` del contrato.
- Idempotencia separada por consumidor y por clave.
- Endpoint de salud `GET /health`.
- Script de carga inicial con los tres artículos del blog.
- Cliente JS (`api.js`), portada dinámica (`notes.js`), artículo dinámico
  (`articulo.html`) y consola de administración (`admin.html`).

## Requisitos

- Python 3.10+ (probado con 3.12).
- Navegador moderno.
- No hace falta instalar un servidor de base de datos.

## Arranque rápido

```bash
cd API/devblog-cms-api-1.2/devblog-cms-api

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Linux / macOS
# python3 -m venv .venv && source .venv/bin/activate
# pip install -r requirements.txt

copy .env.example .env      # Windows (Linux/macOS: cp .env.example .env)
python -m app.seed          # carga los 3 artículos de ejemplo
uvicorn app.main:app --reload --port 8080
```

- Documentación interactiva: <http://127.0.0.1:8080/docs>
- Salud: <http://127.0.0.1:8080/health>
- Base de datos: `data/devblog.db`

> El CMS usa **8080** para coexistir con el colector de métricas (8000) y el
> generador estático (8001) del ecosistema del profesor.

### Frontend

En otra terminal:

```bash
cd dev-blog
python -m http.server 5500
```

- Blog: <http://127.0.0.1:5500/>
- Artículo dinámico: <http://127.0.0.1:5500/articulo.html?slug=despliega-tu-web-gratis-en-vercel>
- Consola CMS: <http://127.0.0.1:5500/admin.html>
  - Token de desarrollo: `console-dev-token`
- Artefactos estáticos generados: `dev-blog/generated/{slug}.html`
- Beacon de métricas: `dev-blog/metrics.js` (se carga en la portada, el artículo
  dinámico y las páginas de artículo existentes).

> Abre el sitio con `http://localhost:5500` o `http://127.0.0.1:5500`, no con
> `file://`, para que CORS y `sessionStorage` funcionen de forma consistente.

## Servicios del ecosistema

El CMS se integra con los dos servicios del ecosistema del profesor. Los tres
pueden convivir en la misma máquina:

| Servicio | Puerto | URL principal | Rol |
|---|---|---|---|
| CMS API (este repo) | 8080 | <http://127.0.0.1:8080> | Borradores, publicaciones y vistas propias. |
| Metrics Collector & Retriever | 8000 | <http://127.0.0.1:8000> | Beacon, tráfico, agentes y GraphQL. |
| Static Sites Generator | 8001 | <http://127.0.0.1:8001> | Compila snapshots en artefactos HTML. |
| Blog estático | 5500 | <http://127.0.0.1:5500> | Consumidor público. |

### Metrics Collector & Retriever

```bash
cd pendiente/metrics-navigation-main/metrics-navigation-main
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Salud: <http://127.0.0.1:8000/health>
- GraphiQL: <http://127.0.0.1:8000/v1/query>
- Demo del beacon: <http://127.0.0.1:8000/v1/demo>
- Configuración local: `STORAGE=memory` (sin MongoDB; los datos se reinician
  al reiniciar el proceso) y `config/bootstrap.devblog.yaml`, que crea el sitio
  `devblog` y su canal beacon para el blog en 5500.
- El blog carga el beacon con `dev-blog/metrics.js` y la clave pública
  `pk_live_devblog_...` de `api-config.js`.

### Static Sites Generator

```bash
cd pendiente/static-sites-generator-main/static-sites-generator-main
.venv\Scripts\activate
uvicorn src.main:app --host 127.0.0.1 --port 8001
```

- Swagger: <http://127.0.0.1:8001/docs>
- Salud: <http://127.0.0.1:8001/health>
- La consola CMS tiene el botón **Generar HTML estático** para un borrador o
  una publicación.
- Para generar todos los artículos publicados de una vez:

```bash
python scripts/generate_static.py
```

Los artefactos se guardan en `dev-blog/generated/{slug}.html` y también quedan
servidos por el generador en `/api/v1/pages/{page_id}/content`.

### Notas de despliegue local

- Para levantar los cuatro servicios de una vez, desde la raíz del proyecto:
  `.\start-all.ps1`.
- La guía detallada está en `pendiente/README_DESPLIEGUE.md`.
- No se usó Docker porque no está instalado en la máquina; ambos servicios
  corren con Python 3.12 en entornos virtuales separados.
- En el repo de métricas se corrigieron dos detalles de despliegue local:
  `detectar_entorno` ahora reconoce loopback con puerto (`127.0.0.1:5500`) y
  CORS permite credenciales para que funcione `navigator.sendBeacon`.
- Pruebas: **43** del CMS, **13** de métricas y **4** del generador.

## Tokens de desarrollo

| Token | Actor | Scopes | Límite |
|---|---|---|---|
| `console-dev-token` | Consola de Administración | `cms:write` | 60 / min |
| `public-dev-token` | Sitio Web Público | `posts:read`, `posts:view` | 10 / s |

Se cambian con `CMS_CONSOLE_TOKEN` y `CMS_PUBLIC_TOKEN` en `.env`.
**No uses los valores por defecto en producción.**

El token público es visible en `dev-blog/api-config.js` porque el navegador lo
necesita. Es de solo lectura y está limitado a 10 peticiones/s. El token de la
consola **no** se escribe en el código: se introduce en `admin.html` y se guarda
solo en `sessionStorage` mientras dura la pestaña.

## Configuración (`.env`)

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `CMS_APP_NAME` | `DevBlog CMS API` | Nombre que aparece en `/docs`. |
| `CMS_ENV` | `development` | `production` activa avisos de seguridad. |
| `CMS_DB_PATH` | `data/devblog.db` | Archivo SQLite. Usa `:memory:` solo en pruebas. |
| `CMS_CONSOLE_TOKEN` | `console-dev-token` | Token de escritura. |
| `CMS_PUBLIC_TOKEN` | `public-dev-token` | Token de lectura/vistas. |
| `CMS_CURSOR_SECRET` | valor de desarrollo | Secreto HMAC de los cursores. |
| `CMS_CORS_ORIGINS` | orígenes locales | Orígenes permitidos, separados por coma. |
| `CMS_PUBLIC_SITE_URL` | vacío | Dominio público para construir `url` absoluta. |
| `CMS_PUBLIC_ARTICLE_PATH` | `/blog/{slug}` | Ruta del artículo; debe contener `{slug}`. |
| `CMS_IDEMPOTENCY_TTL_S` | `86400` | Ventana de idempotencia. |
| `CMS_CONSOLE_RATE_LIMIT` | `60` | Peticiones por ventana de la consola. |
| `CMS_PUBLIC_RATE_LIMIT` | `10` | Peticiones por ventana del sitio. |
| `CMS_LOG_LEVEL` | `INFO` | Nivel de logs. |

Para el blog estático se usa:

```env
CMS_PUBLIC_ARTICLE_PATH=/articulo.html?slug={slug}
```

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `app/config.py` | Configuración, tokens, scopes y límites. |
| `app/schemas.py` | Modelos Pydantic de entrada/salida y validaciones. |
| `app/domain.py` | Entidad `Post`, estados, UUIDv7, slug y tiempo de lectura. |
| `app/services.py` | Reglas de negocio e invariantes (Paso 3). |
| `app/repository.py` | Interfaz `PostRepository` + implementación en memoria. |
| `app/sqlite_repository.py` | Implementación SQLite (persistencia real). |
| `app/routers/drafts.py` | Endpoints 1-6 (`/drafts`). |
| `app/routers/posts.py` | Endpoints 7-12 (`/posts`). |
| `app/routers/health.py` | `GET /health`. |
| `app/errors.py` | Formato de error único y captura de 500. |
| `app/dependencies.py` | Autenticación, scopes, rate limit, idempotencia. |
| `app/infra.py` | Limitador de tráfico e idempotencia en memoria. |
| `app/caching.py` | `ETag`, `Cache-Control` y 304. |
| `app/pagination.py` | Cursor opaco firmado (id + timestamp). |
| `app/seed.py` | Carga inicial de artículos. |
| `scripts/generate_static.py` | Genera artefactos HTML en el servicio de 8001. |

## Endpoints

| # | Método | Ruta | Actor |
|---|---|---|---|
| 1 | POST | `/api/v1/drafts` | Consola |
| 2 | GET | `/api/v1/drafts` | Consola |
| 3 | GET | `/api/v1/drafts/{post_id}` | Consola |
| 4 | PUT | `/api/v1/drafts/{post_id}` | Consola |
| 5 | DELETE | `/api/v1/drafts/{post_id}` | Consola |
| 6 | POST | `/api/v1/drafts/{post_id}/publish` | Consola |
| 7 | GET | `/api/v1/posts` | Consola / Sitio |
| 8 | GET | `/api/v1/posts/{post_id}` | Consola / Sitio |
| 9 | GET | `/api/v1/posts/slug/{slug}` | Consola / Sitio |
| 10 | DELETE | `/api/v1/posts/{post_id}` | Consola |
| 11 | GET | `/api/v1/posts/{post_id}/metrics` | Consola |
| 12 | POST | `/api/v1/posts/{post_id}/views` | Sitio |

Además: `GET /health` (sin token) y `/docs` (Swagger UI).

## Persistencia y datos

- SQLite guarda todo en `data/devblog.db`.
- El seed carga versiones Markdown resumidas de los tres artículos. Las páginas
  interactivas originales (`articulo-cpp.html`, `articulo-voz.html`,
  `articulo-vercel.html`) siguen disponibles y el artículo dinámico enlaza a
  ellas con "Ver versión interactiva".
- Para reiniciar el contenido: borra el archivo y vuelve a ejecutar
  `python -m app.seed`.
- Para respaldar: copia el archivo `.db` (idealmente con la API detenida).
- `app/seed.py` es idempotente: no duplica artículos existentes.

## Cursor firmado

El cursor sigue siendo opaco para el cliente. Internamente tiene dos partes:

```
<payload_base64url>.<firma_hmac_base64url>
```

La parte decodificable mantiene la estructura documentada:

```json
{"id": "0192a3b5-1122-7334-8445-556677889900", "published_at": "2026-10-15T18:30:00Z"}
```

Si alguien altera el payload o la firma, la API responde
`422 INVALID_CURSOR`. Esto cumple la regla de la especificación: un cursor
alterado no puede aceptarse solo porque parezca JSON válido.

## Reutilizar la API en otro proyecto

El código no está atado al DevBlog. Para usarlo en otro proyecto:

1. Copia esta carpeta.
2. Crea un `.env` nuevo.
3. Cambia `CMS_APP_NAME`, `CMS_CONSOLE_TOKEN`, `CMS_PUBLIC_TOKEN`,
   `CMS_CURSOR_SECRET`, `CMS_DB_PATH` y `CMS_CORS_ORIGINS`.
4. Ajusta `CMS_PUBLIC_ARTICLE_PATH` a la ruta de artículo de ese proyecto.
5. Si usas otra base de datos, implementa `PostRepository` y pásala en
   `create_app(repository=...)`; el servicio y los routers no cambian.

No se añadió un campo `site_id` porque el contrato v1.2 es de un solo blog. Si
algún día necesitas varias instalaciones en una sola API, ese sería un cambio
de modelo y requeriría una nueva versión del contrato.

## Pruebas

```bash
pytest -q
```

La suite cubre el contrato completo, la persistencia entre reinicios, el cursor
firmado, CORS, salud y el formato de errores 500.

Los servicios del ecosistema tienen sus propias pruebas:

```bash
cd pendiente/metrics-navigation-main/metrics-navigation-main
.venv\Scripts\python.exe -m pytest tests -q

cd pendiente/static-sites-generator-main/static-sites-generator-main
.venv\Scripts\python.exe -m unittest tests/test_api.py -v
```

## Seguridad y limitaciones

- Los tokens por defecto son de desarrollo. Cámbialos en producción.
- El token público está en el navegador: es de solo lectura y está limitado.
- No hay usuario/contraseña: el contrato define tokens Bearer emitidos por un
  servicio externo. La consola de este proyecto pide el token manualmente.
- El rate limit y la idempotencia viven en memoria **por proceso**. Con varias
  instancias hay que moverlos a Redis u otro almacén compartido.
- El timeout de 10 s del contrato lo debe aplicar el servidor/proxy; la app no
  simula un 504.
- El borrado de publicaciones es físico e irreversible, como indica el contrato.
- El colector de métricas corre con `STORAGE=memory`: los eventos se pierden al
  reiniciar. Para persistirlos, configura `STORAGE=mongo` y `MONGO_URI`.
- El generador estático no tiene autenticación y su CORS es abierto; está pensado
  para local. En producción debe quedar detrás de un proxy/autenticación.
- Los artefactos del generador son HTML simple con el contenido en `<pre>`; la
  página dinámica del blog sigue siendo la versión con el diseño del DevBlog_.

## Solución de problemas

**El blog muestra las tarjetas locales.**
La API no está disponible. Comprueba `http://127.0.0.1:8080/health` y que
`CMS_CORS_ORIGINS` incluya el origen del blog (`http://127.0.0.1:5500`).
Si lo que falla es el beacon, comprueba `http://127.0.0.1:8000/health` y
`http://127.0.0.1:8001/health` para métricas y generador, respectivamente.

**`401 UNAUTHORIZED` en la consola.**
El token no coincide con `CMS_CONSOLE_TOKEN`. Usa `console-dev-token` en
desarrollo o el valor de tu `.env`.

**`429 RATE_LIMITED`.**
Se superó el límite (60/min consola, 10/s sitio). Espera el `Retry-After`.

**`SLUG_DUPLICATED`.**
El slug ya pertenece a otro Post, aunque sea un borrador. Cambia el slug.

**La base está bloqueada.**
Cierra otras instancias de la API que estén usando el mismo `.db`. SQLite usa
WAL y `busy_timeout`, pero no admite escrituras simultáneas de varios procesos
por largos periodos.
