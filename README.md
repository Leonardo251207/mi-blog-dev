# DevBlog_ — CMS, blog y servicios del ecosistema

Proyecto completo para la asignatura de Aplicaciones Web:

- **CMS DevBlog** en FastAPI con persistencia SQLite.
- **Blog estático** conectado al CMS.
- **Consola de administración** para crear, editar, publicar y medir artículos.
- **Metrics Collector & Retriever** del ecosistema del profesor (beacon + GraphQL).
- **Static Sites Generator** del ecosistema del profesor (artefactos HTML).
- Documentación del contrato v1.2 + Anexo D de implementación y servicios.

## Puertos

| Servicio | Puerto | URL |
|---|---:|---|
| CMS DevBlog | 8080 | <http://127.0.0.1:8080> |
| Métricas | 8000 | <http://127.0.0.1:8000> |
| Generador estático | 8001 | <http://127.0.0.1:8001> |
| Blog | 5500 | <http://127.0.0.1:5500> |

## Requisitos

- Windows con PowerShell.
- Python 3.12 o superior.
- Git.
- Opcional: [`uv`](https://docs.astral.sh/uv/) para crear entornos más rápido.
  El script `setup.ps1` funciona con `uv` o con `python -m venv`.

> No se necesita Docker. Los servicios se ejecutan con Python nativo.

## Clonar y preparar en otra laptop

```powershell
git clone https://github.com/Leonardo251207/mi-blog-dev.git
cd mi-blog-dev
.\setup.ps1
```

> Si PowerShell bloquea la ejecución de scripts, abre la sesión con:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

`setup.ps1` hace lo siguiente:

1. Crea los entornos `.venv` del CMS, Métricas y Generador.
2. Instala las dependencias de cada servicio.
3. Copia los `.env.example` a `.env` si faltan.
4. Carga los tres artículos de ejemplo en la base SQLite del CMS.

Después, para levantar todo:

```powershell
.\start-all.ps1
```

Se abren cuatro ventanas de PowerShell: CMS, Métricas, Generador y Blog.

## Despliegue gratuito del blog

El blog es estático y se puede publicar gratis en **GitHub Pages** o **Vercel**.
Los servicios del CMS, métricas y generador son Python y necesitan ejecutarse
aparte (localmente o en un host Python con HTTPS).

### GitHub Pages

Ya está incluido el workflow `.github/workflows/pages.yml`.

1. En GitHub, entra a **Settings → Pages**.
2. En **Source**, selecciona **GitHub Actions**.
3. Haz push a `main` o ejecuta manualmente el workflow
   **Deploy blog to GitHub Pages**.
4. La URL será:

   <https://leonardo251207.github.io/mi-blog-dev/>

### Vercel

1. Importa el repositorio <https://github.com/Leonardo251207/mi-blog-dev>.
2. Framework Preset: **Other**.
3. Root Directory: `dev-blog` (o deja la raíz; el `vercel.json` ya apunta a
   `dev-blog`).
4. Build Command: vacío.
5. Output Directory: `dev-blog` (o `.` si usaste Root Directory `dev-blog`).
6. Deploy.

### Importante

- En Pages/Vercel solo se publica el **blog estático**. La portada intentará
  llamar a `http://127.0.0.1:8080` y `http://127.0.0.1:8000`; si no están
  disponibles, `notes.js` muestra las tarjetas estáticas de respaldo.
- El artículo dinámico (`articulo.html?slug=...`) y `admin.html` necesitan la
  API del CMS. Para usarlos desde internet hay que desplegar el CMS (y
  opcionalmente métricas/generador) en un host Python con HTTPS, cambiar
  `API_BASE_URL`, `METRICS_BASE_URL` y `STATIC_GENERATOR_BASE_URL` en
  `dev-blog/api-config.js`, y agregar el dominio del blog a `CMS_CORS_ORIGINS`
  y `CORS_ORIGINS`.
- Las páginas `articulo-cpp.html`, `articulo-voz.html` y `articulo-vercel.html`
  sí funcionan sin API.

## URLs útiles

- CMS / Swagger: <http://127.0.0.1:8080/docs>
- Salud del CMS: <http://127.0.0.1:8080/health>
- Métricas / GraphiQL: <http://127.0.0.1:8000/v1/query>
- Salud de Métricas: <http://127.0.0.1:8000/health>
- Generador / Swagger: <http://127.0.0.1:8001/docs>
- Salud del Generador: <http://127.0.0.1:8001/health>
- Blog: <http://127.0.0.1:5500/>
- Consola CMS: <http://127.0.0.1:5500/admin.html>

## Tokens de desarrollo

| Token | Actor | Scopes | Límite |
|---|---|---|---|
| `console-dev-token` | Consola CMS | `cms:write` | 60/min |
| `public-dev-token` | Blog público | `posts:read`, `posts:view` | 10/s |

El token de la consola se escribe en `admin.html` y se guarda solo en
`sessionStorage`. El token público está en `dev-blog/api-config.js`.

## Estructura

```text
mi-blog-dev/
├── API/
│   └── devblog-cms-api-1.2/
│       ├── devblog-cms-api/          # FastAPI, SQLite y pruebas
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
├── start-all.ps1
├── setup.ps1
└── README.md
```

## Integración

### Blog → CMS

- La portada pide `GET /api/v1/posts` al CMS en 8080.
- El artículo dinámico usa `GET /api/v1/posts/slug/{slug}`.
- La vista propia se registra con `POST /api/v1/posts/{post_id}/views`.

### Blog → Métricas

- `dev-blog/metrics.js` inyecta `/v1/beacon.js` del servicio en 8000.
- El beacon envía pageviews y engagement al sitio `devblog`.
- Las consultas reales de tráfico se hacen por GraphQL en
  <http://127.0.0.1:8000/v1/query>.

### Consola → Generador estático

- La consola tiene el botón **Generar HTML estático**.
- También se pueden generar todos los artículos publicados:

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\activate
python scripts\generate_static.py
```

Los artefactos se guardan en `dev-blog/generated/{slug}.html` y también quedan
servidos por el generador en `/api/v1/pages/{page_id}/content`.

## Pruebas

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

## Documentación

- Contrato original + Anexo D:
  - `API/Especificacion_API_CMS_DevBlog_v1.2_implementacion.docx`
  - `API/Especificacion_API_CMS_DevBlog_v1.2_implementacion.pdf`
- Guía de despliegue de los servicios:
  - `pendiente/README_DESPLIEGUE.md`
- README del CMS:
  - `API/devblog-cms-api-1.2/devblog-cms-api/README.md`

## Notas

- El colector de métricas corre con `STORAGE=memory`: los eventos se pierden al
  reiniciar. Para persistirlos se configura `STORAGE=mongo` y `MONGO_URI`.
- El generador estático no tiene autenticación y su CORS es abierto; está
  pensado para local. En producción debe quedar detrás de un proxy/autenticación.
- El endpoint REST `/api/v1/documents/{id}/metrics` del repo de métricas sigue
  devolviendo valores de ejemplo; el tráfico real se consulta por GraphQL.
- Se corrigieron dos detalles de despliegue local en el repo de métricas:
  `detectar_entorno` reconoce loopback con puerto y CORS permite credenciales
  para `navigator.sendBeacon`.
- El contenido antiguo de `mi-blog-dev` fue reemplazado por esta versión. El
  historial anterior sigue disponible en los commits del repositorio.
