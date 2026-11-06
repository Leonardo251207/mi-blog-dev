# Guía local y de integración

Esta guía explica cómo ejecutar el proyecto completo en tu laptop, cómo se
conectan los servicios y cómo probar cada pieza. Para publicarlo en internet,
consulta [`../DEPLOY_RENDER.md`](../DEPLOY_RENDER.md).

## Requisitos

- Windows con PowerShell.
- Python 3.12 o superior.
- Git.
- Opcional: [`uv`](https://docs.astral.sh/uv/) para crear entornos más rápido.
  `setup.ps1` funciona con `uv` o con `python -m venv`.

> No se necesita Docker para el desarrollo local.

## Clonar y preparar

```powershell
git clone https://github.com/Leonardo251207/mi-blog-dev.git
cd mi-blog-dev
.\setup.ps1
```

Si PowerShell bloquea la ejecución de scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

`setup.ps1`:

1. Crea los entornos `.venv` del CMS, Métricas y Generador.
2. Instala las dependencias de cada servicio.
3. Copia los `.env.example` a `.env` si faltan.
4. Carga los tres artículos de ejemplo en SQLite (o en Mongo si configuras
   `CMS_MONGO_URI`).

## Levantar todo

```powershell
.\start-all.ps1
```

Se abren cuatro ventanas de PowerShell:

| Servicio | Puerto | URL local |
|---|---:|---|
| CMS | 8080 | <http://127.0.0.1:8080> |
| Métricas + GraphQL | 8000 | <http://127.0.0.1:8000> |
| Generador estático | 8001 | <http://127.0.0.1:8001> |
| Blog | 5500 | <http://127.0.0.1:5500> |

Para detenerlos, cierra cada ventana o pulsa `Ctrl+C`.

## URLs locales

- CMS / Swagger: <http://127.0.0.1:8080/docs>
- Salud del CMS: <http://127.0.0.1:8080/health>
- Métricas / GraphiQL: <http://127.0.0.1:8000/v1/query>
- Salud de Métricas: <http://127.0.0.1:8000/health>
- Generador / Swagger: <http://127.0.0.1:8001/docs>
- Salud del Generador: <http://127.0.0.1:8001/health>
- Blog: <http://127.0.0.1:5500/>
- Consola CMS: <http://127.0.0.1:5500/admin.html>

## Tokens

### Local

| Token | Actor | Scopes |
|---|---|---|
| `console-dev-token` | Consola CMS | `cms:write` |
| `public-dev-token` | Blog público | `posts:read`, `posts:view` |

### Producción

- El token público de producción está en `dev-blog/api-config.js`:
  `pub_live_devblog_2026`.
- El token de la consola lo genera Render en
  `devblog-cms-leonardo → Environment → CMS_CONSOLE_TOKEN`.
- El token de la consola **no** se guarda en el repositorio.

`api-config.js` detecta si estás en `localhost`/`127.0.0.1` y usa los tokens y
URLs locales; en Vercel/GitHub Pages usa los servicios de Render.

## Estructura

```text
mi-blog-dev/
├── API/
│   └── devblog-cms-api-1.2/
│       ├── devblog-cms-api/          # FastAPI, Mongo/SQLite, tests y scripts
│       └── Especificacion_...docx/.pdf
├── dev-blog/                         # Blog estático + consola CMS
│   ├── index.html
│   ├── articulo.html
│   ├── admin.html
│   ├── api.js / api-config.js
│   ├── metrics.js                    # Beacon de métricas
│   └── generated/                    # Artefactos HTML del generador
├── pendiente/
│   ├── metrics-navigation-main/      # Servicio de métricas
│   ├── static-sites-generator-main/  # Generador estático
│   └── README_DESPLIEGUE.md
├── docs/
│   ├── banner.svg
│   └── GUIA_LOCAL.md
├── DEPLOY_RENDER.md
├── render.yaml
├── start-all.ps1
├── setup.ps1
└── README.md
```

## Integración

### Blog → CMS

- La portada pide `GET /api/v1/posts` al CMS.
- El artículo dinámico usa `GET /api/v1/posts/slug/{slug}`.
- La vista propia se registra con `POST /api/v1/posts/{post_id}/views`.
- Si la API no responde, `notes.js` muestra las tarjetas estáticas de respaldo.

### Blog → Métricas

- `dev-blog/metrics.js` inyecta `/v1/beacon.js` del colector.
- El beacon envía pageviews y engagement al sitio `devblog`.
- Las consultas reales se hacen por GraphQL en `/v1/query`.

### Consola → Generador

- La consola tiene el botón **Generar HTML estático**.
- También puedes generar todos los artículos publicados:

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\activate
python scripts\generate_static.py
```

Los artefactos se guardan en `dev-blog/generated/{slug}.html` y también quedan
servidos por el generador en `/api/v1/pages/{page_id}/content`.

## Persistencia

- **Local**: SQLite en `data/devblog.db` (no se versiona).
- **Producción**: MongoDB Atlas si `CMS_MONGO_URI` está definido.
- **Métricas**: Mongo Atlas en producción; `STORAGE=memory` si no hay Mongo.
- **Generador**: disco local/efímero; los artefactos se pueden regenerar.

Para usar Mongo en local, agrega a `API/.../.env`:

```env
CMS_MONGO_URI=mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
CMS_MONGO_DB=devblog_cms
```

## Pruebas

```powershell
# CMS: 47 pruebas (43 del contrato + 4 del repositorio Mongo)
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\python.exe -m pytest -q

# Métricas: 13 pruebas
cd pendiente\metrics-navigation-main\metrics-navigation-main
.venv\Scripts\python.exe -m pytest tests -q

# Generador: 4 pruebas
cd pendiente\static-sites-generator-main\static-sites-generator-main
.venv\Scripts\python.exe -m unittest tests/test_api.py -v
```

## Documentación

- Despliegue en Render + Atlas: [`../DEPLOY_RENDER.md`](../DEPLOY_RENDER.md)
- Servicios del ecosistema: [`../pendiente/README_DESPLIEGUE.md`](../pendiente/README_DESPLIEGUE.md)
- README del CMS: [`../API/devblog-cms-api-1.2/devblog-cms-api/README.md`](../API/devblog-cms-api-1.2/devblog-cms-api/README.md)
- Contrato + Anexo D:
  - `API/Especificacion_API_CMS_DevBlog_v1.2_implementacion.docx`
  - `API/Especificacion_API_CMS_DevBlog_v1.2_implementacion.pdf`

## Problemas comunes

**El blog muestra las tarjetas locales.**
La API no está disponible. Comprueba `/health` del CMS o de Render.

**`401 UNAUTHORIZED` en la consola.**
Usa el token correcto: `console-dev-token` en local; el generado por Render en
producción.

**`429 RATE_LIMITED`.**
Espera el `Retry-After`; los límites son 60/min consola y 10/s sitio público.

**`SLUG_DUPLICATED`.**
El slug ya existe en un borrador o publicación.

**Error de CORS en producción.**
Agrega el origen exacto del blog a `CMS_CORS_ORIGINS` y `CORS_ORIGINS`, y
redespliega.

**Render tarda en responder.**
Los servicios gratuitos se duermen; la primera petición puede tardar 30–60 s.

## Notas

- El endpoint REST `/api/v1/documents/{id}/metrics` del repo de métricas sigue
  devolviendo valores de ejemplo; el tráfico real se consulta por GraphQL.
- El generador estático no tiene autenticación y su CORS es abierto; es un
  servicio de demostración.
- Se corrigieron dos detalles de despliegue local en el repo de métricas:
  `detectar_entorno` reconoce loopback con puerto y CORS permite credenciales
  para `navigator.sendBeacon`.
