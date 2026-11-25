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
   `CMS_MONGO_URI`), además de la landing inicial y una publicidad de ejemplo.

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
- Landing pública: <http://127.0.0.1:8080/api/v1/landing>
- Métricas / GraphiQL: <http://127.0.0.1:8000/v1/query>
- Salud de Métricas: <http://127.0.0.1:8000/health>
- Generador / Swagger: <http://127.0.0.1:8001/docs>
- Salud del Generador: <http://127.0.0.1:8001/health>
- Blog: <http://127.0.0.1:5500/>
- Consola CMS: <http://127.0.0.1:5500/admin.html>

La landing/portafolio vive en un repositorio aparte
([`mi-landing-devblog`](https://github.com/Leonardo251207/mi-landing-devblog)).
Para verla en local:

```powershell
cd ..\mi-landing-devblog
python -m http.server 5599
```

Luego abre <http://127.0.0.1:5599/>. La landing consume el CMS de
`127.0.0.1:8080` y, si no está disponible, conserva su HTML estático.

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
│   ├── index.html                    # Portada del blog (últimas entradas)
│   ├── articulo.html                 # Artículo dinámico por slug
│   ├── admin.html                    # Consola: dashboard, blog, landing, publicidad y métricas
│   ├── dashboard.js / dashboard.css  # Dashboard analítico
│   ├── editor-pro.js / editor-pro.css# Editor enriquecido
│   ├── api.js / api-config.js
│   ├── metrics.js                    # Beacon de métricas
│   └── generated/                    # Artefactos HTML del generador
├── pendiente/
│   ├── metrics-navigation-main/      # Servicio de métricas
│   ├── static-sites-generator-main/  # Generador estático
│   └── README_DESPLIEGUE.md
├── docs/
│   ├── banner.svg
│   ├── GUIA_LOCAL.md
│   └── GUION_VIDEO.md
├── DEPLOY_RENDER.md
├── render.yaml
├── start-all.ps1
├── setup.ps1
└── README.md
```

El repo de la landing tiene su propia estructura:

```text
mi-landing-devblog/
├── index.html            # Landing profesional editable
├── sitio.html            # Renderer genérico multi-sitio + videos
├── landing.js            # Aplica la landing del portafolio
├── sitio.js              # Carga cualquier sitio por ?site=slug
├── sitio.css             # Estilos de videos y renderer
├── notes.js              # Últimas notas del blog
├── api.js / api-config.js
├── metrics.js
├── styles.css / script.js
├── assets/               # Foto de perfil y certificados PDF
└── .github/workflows/    # GitHub Pages
```

## Integración

### Blog → CMS

- La portada del blog pide `GET /api/v1/posts` al CMS.
- El artículo dinámico usa `GET /api/v1/posts/slug/{slug}`.
- La vista propia se registra con `POST /api/v1/posts/{post_id}/views`.
- Si la API no responde, `notes.js` conserva las tarjetas estáticas de respaldo.

### Landing → CMS

- El portafolio pide `GET /api/v1/landing` y `landing.js` aplica el contenido
  publicado y la publicidad activa sobre `index.html`.
- Las demás landings usan `sitio.html?site={slug}` y
  `GET /api/v1/sites/{slug}/landing`. El renderer aplica el tema del sitio y
  pinta hero, tecnologías, proyectos, videos, certificaciones y contacto.
- Si la API no responde (o el origen no está en CORS), el portafolio conserva su
  HTML estático y sigue navegable.

### Sitios → CMS (multi-landing)

- `GET /api/v1/sites` lista los sitios públicos activos.
- `GET /api/v1/sites/admin` lista todos (consola).
- `POST /api/v1/sites` crea un sitio y genera su landing base publicada.
- `PUT /api/v1/sites/{site_id}` y `DELETE /api/v1/sites/{site_id}` administran
  la propiedad.
- `GET /api/v1/sites/{site_id}/landing` devuelve `{site, content, ads}`.
- La consola usa `/sites/{site_id}/landing/draft` y
  `/sites/{site_id}/landing/publish` para borrador y publicación por sitio.
- Los sitios base `portfolio` y `devblog` están protegidos contra borrado.

### Consola → CMS (landing y publicidad)

- **Landing y publicidad** carga el borrador con `GET /api/v1/landing/draft`.
- **Guardar borrador** usa `PUT /api/v1/landing/draft`; **Publicar landing**
  usa `POST /api/v1/landing/publish`. El sitio público solo ve lo publicado.
- La publicidad se administra con `GET /api/v1/ads/admin`, `POST /api/v1/ads`,
  `PUT /api/v1/ads/{ad_id}` y `DELETE /api/v1/ads/{ad_id}`.
- La ruta pública `GET /api/v1/ads` solo devuelve anuncios activos.

### Blog → Métricas

- `dev-blog/metrics.js` inyecta `/v1/beacon.js` del colector.
- El beacon envía pageviews y engagement al sitio `devblog`.
- Las consultas reales se hacen por GraphQL en `/v1/query`.
- La consola pide `GET /api/v1/metrics/overview` al CMS; el backend consulta
  `CMS_METRICS_URL` por GraphQL. Así se evita CORS y el navegador no necesita
  conocer la URL interna del colector.

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

## Consola: dashboard y editor

La consola adapta el panel del profesor (`cms-view`) a la API y al estilo de
DevBlog_:

### Dashboard

- **Sitio**: Todos, DevBlog_ o Portafolio. También puedes agregar dominios
  propios; se guardan en `localStorage`.
- **Periodo**: 1 día, 1 semana, 2 semanas, 1 mes, 3 meses o 1 año.
- **Resumen**: pageviews, visitantes únicos, sesiones y tiempo promedio de
  lectura.
- **Artículos más leídos**: vistas acumuladas de cada publicación.
- **Distribución**: pageviews por host o por ruta, en pastel o dona.
- **Ranking**: búsqueda, límite y exportación CSV.
- Si el colector no responde, el dashboard muestra las vistas del CMS y un
  aviso de error.

### Editor

- Portada por URL o archivo local.
- Barra para insertar párrafo, H2, H3, código, nota, lista, cita, imagen y
  divisor.
- Vista dividida, solo editor o solo vista previa.
- Inspector: publicación (estado, categoría, autor, fecha), tipografía, SEO e
  índice.
- Autoguardado local y exportación Markdown/JSON.
- `Ctrl+S` guarda el borrador cuando el editor está activo.

> El contrato del CMS guarda título, slug, etiquetas y Markdown. Portada, SEO,
> tipografía y estado “en revisión” viven en `localStorage` porque el contrato
> v1.2 no tiene esos campos. El estado real de publicación sigue siendo el del
> CMS.

## Persistencia

- **Local**: SQLite en `data/devblog.db` (no se versiona). Guarda posts,
  sitios, landings por sitio (borrador/publicada), publicidad y metadatos de
  seed.
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
# CMS: 61 pruebas (contrato, contenido, sitios y repositorio Mongo)
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\python.exe -m pytest -q

# Métricas: 13 pruebas
cd pendiente\metrics-navigation-main\metrics-navigation-main
.venv\Scripts\python.exe -m pytest tests -q

# Generador: 4 pruebas
cd pendiente\static-sites-generator-main\static-sites-generator-main
.venv\Scripts\python.exe -m unittest tests/test_api.py -v
```

Total del ecosistema: **74 pruebas**.

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
Agrega el origen exacto del blog **y de la landing** a `CMS_CORS_ORIGINS` y
`CORS_ORIGINS`, y redespliega. La landing necesita, además de su URL de Vercel,
el origen de GitHub Pages (`https://leonardo251207.github.io`). Si publicas una
landing de cliente en un dominio propio, agrega también ese dominio.

**Guardé la landing pero el sitio sigue igual.**
El cambio queda como borrador. Pulsa **Publicar landing**. La lectura pública
tiene caché de 60 s.

**La consola dice «Métricas no disponibles».**
Comprueba que el servicio de métricas esté corriendo en `127.0.0.1:8000` y que
`CMS_METRICS_URL`/`CMS_METRICS_SITE=devblog` sean correctos. El CMS consulta
GraphQL desde el backend; no es un problema de CORS del navegador.

**La publicidad no aparece.**
Debe estar **activa**. La ruta pública solo devuelve anuncios activos.

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
