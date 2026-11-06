# Despliegue en internet: Render + MongoDB Atlas

Esta guía publica el CMS, las métricas/GraphQL y el generador estático en
**Render** (capa gratuita) con persistencia en **MongoDB Atlas** (M0 gratuita).
El blog ya está en Vercel y GitHub Pages.

## Arquitectura

```text
Vercel / GitHub Pages (blog estático)
        │
        ├── https://devblog-cms-leonardo.onrender.com       → CMS FastAPI
        ├── https://devblog-metrics-leonardo.onrender.com   → Métricas + GraphQL
        └── https://devblog-generator-leonardo.onrender.com → Generador HTML

CMS y Métricas → MongoDB Atlas (M0)
```

| Servicio | Plan | Persistencia |
|---|---|---|
| CMS | Render Free | MongoDB Atlas |
| Métricas | Render Free | MongoDB Atlas |
| Generador | Render Free | Disco efímero (los artefactos se regeneran) |
| Atlas M0 | Free | 512 MB |

> Los servicios gratuitos de Render se duermen tras unos minutos sin tráfico.
> La primera petición puede tardar 30–60 s. Para presentar, abre las URLs unos
> minutos antes.

---

## 1. Crear MongoDB Atlas (una sola vez)

1. Entra a <https://www.mongodb.com/cloud/atlas/register> y crea una cuenta.
2. Crea un clúster **M0 Free** (provider y región que prefieras).
3. En **Database Access**, crea un usuario con contraseña (rol `Atlas admin`
   o `Read and write to any database`).
4. En **Network Access**, agrega `0.0.0.0/0` para permitir Render.
   - Para un proyecto escolar es aceptable. En producción real se restringe.
5. En **Database → Connect → Drivers**, copia la cadena:

```text
mongodb+srv://USUARIO:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

Esa cadena se usa como `CMS_MONGO_URI` y `MONGO_URI` en Render.

---

## 2. Desplegar los tres servicios en Render

El repositorio ya incluye `render.yaml` en la raíz.

1. Entra a <https://render.com> y crea una cuenta con GitHub.
2. **New → Blueprint**.
3. Conecta el repositorio `Leonardo251207/mi-blog-dev`.
4. Render detecta `render.yaml` y propone tres servicios:
   - `devblog-cms-leonardo`
   - `devblog-metrics-leonardo`
   - `devblog-generator-leonardo`
5. Al aplicar el blueprint, Render pedirá las variables marcadas con
   `sync: false`:
   - `CMS_MONGO_URI` → cadena de Atlas.
   - `MONGO_URI` → la misma cadena de Atlas.
6. Aplica el blueprint y espera los builds.
7. En el panel de `devblog-cms-leonardo`, copia el valor generado de
   `CMS_CONSOLE_TOKEN`. Ese es el token que usarás en `admin.html`.

### URLs esperadas

- CMS / Swagger: <https://devblog-cms-leonardo.onrender.com/docs>
- Salud del CMS: <https://devblog-cms-leonardo.onrender.com/health>
- Métricas / GraphiQL: <https://devblog-metrics-leonardo.onrender.com/v1/query>
- Salud de métricas: <https://devblog-metrics-leonardo.onrender.com/health>
- Generador / Swagger: <https://devblog-generator-leonardo.onrender.com/docs>
- Salud del generador: <https://devblog-generator-leonardo.onrender.com/health>

Si Render le asigna otro nombre a algún servicio, cambia las URLs en
`dev-blog/api-config.js` y haz push.

---

## 3. Verificar el CMS y la base

Abre el Swagger del CMS y prueba:

1. `POST /api/v1/drafts` con `Authorization: Bearer <CMS_CONSOLE_TOKEN>`.
   - Usa el token de consola generado por Render (no el público).
   - Debes enviar `Idempotency-Key`.
2. `POST /api/v1/drafts/{post_id}/publish`.
3. `GET /api/v1/posts` con el token público `pub_live_devblog_2026`.

El CMS ejecuta `python -m app.seed` al arrancar y carga los tres artículos en
Atlas si la base está vacía. Los artículos que crees desde la consola se
guardan en Atlas y sobreviven a reinicios.

---

## 4. Verificar métricas y GraphQL

1. Abre el blog en Vercel o GitHub Pages.
2. Espera unos segundos a que el beacon envíe el pageview.
3. Abre <https://devblog-metrics-leonardo.onrender.com/v1/query>.
4. Ejecuta:

```graphql
{
  sitios { slug nombre estado }
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
  }
}
```

El `CORS_ORIGINS` del servicio ya incluye:
`https://mi-blog-dev.vercel.app`, `https://leonardo251207.github.io` y los
orígenes locales de prueba.

---

## 5. Verificar el frontend

`dev-blog/api-config.js` detecta el host:

- En `localhost`/`127.0.0.1` usa los servicios locales.
- En Vercel/GitHub Pages usa las URLs de Render.

Después de desplegar Render, entra a:

- <https://mi-blog-dev.vercel.app/>
- <https://leonardo251207.github.io/mi-blog-dev/>

Debes ver la portada con las publicaciones reales del CMS (no el respaldo
estático). El artículo dinámico y la consola también deben funcionar.

Si ves el aviso de “contenido estático”, revisa:

- Que las URLs de Render en `api-config.js` sean las correctas.
- Que `CMS_CORS_ORIGINS` incluya el origen exacto del blog.
- Que el CMS esté despierto (la primera petición puede tardar).

---

## 6. Generador estático

La consola tiene el botón **Generar HTML estático**. En producción llama a
`https://devblog-generator-leonardo.onrender.com/api/v1/pages`.

- El generador no tiene autenticación: es un servicio de demostración.
- Su disco es efímero; los artefactos se pierden al reiniciar, pero se pueden
  regenerar desde la consola o con `scripts/generate_static.py`.
- Para una versión más segura, se puede añadir una clave de API al generador.

---

## 7. Variables importantes

### CMS

| Variable | Valor |
|---|---|
| `CMS_MONGO_URI` | Cadena de Atlas (secreto) |
| `CMS_MONGO_DB` | `devblog_cms` |
| `CMS_PUBLIC_TOKEN` | `pub_live_devblog_2026` |
| `CMS_CONSOLE_TOKEN` | Generado por Render (cópialo) |
| `CMS_CURSOR_SECRET` | Generado por Render |
| `CMS_CORS_ORIGINS` | Vercel + GitHub Pages + localhost |
| `CMS_PUBLIC_SITE_URL` | `https://mi-blog-dev.vercel.app` |

### Métricas

| Variable | Valor |
|---|---|
| `STORAGE` | `mongo` |
| `MONGO_URI` | Cadena de Atlas (secreto) |
| `MONGO_DB` | `metrics` |
| `BOOTSTRAP_FILE` | `config/bootstrap.prod.yaml` |
| `APP_ENV` | `local` (mantiene GraphiQL visible) |
| `CORS_ORIGINS` | Vercel + GitHub Pages + localhost |

### Generador

| Variable | Valor |
|---|---|
| `PORT` | Lo inyecta Render |
| `PYTHON_VERSION` | `3.12.6` |

---

## 8. Actualizar el repositorio

Cada push a `main`:

- Vercel y GitHub Pages reconstruyen el blog.
- Render puede reconstruir los servicios si tienen **Auto-Deploy** activo.

Para cambios de configuración del CMS o métricas, edita las variables en el
panel de Render y guarda; el servicio se reinicia.

---

## 9. Costos y límites

- Render Free: 750 horas de instancia al mes por workspace; los servicios se
  duermen sin tráfico. Tres servicios encendidos 24/7 superarían ese límite,
  pero con sueño por inactividad es suficiente para una entrega.
- MongoDB Atlas M0: 512 MB gratuitos.
- Vercel Hobby y GitHub Pages: gratuitos para el blog estático.
- Si más adelante quieres persistencia para el generador o evitar el sueño de
  Render, se puede pasar a un plan pago pequeño o a un VPS con Docker.

---

## 10. Problemas comunes

### `bad auth : authentication failed`

Es el error de Atlas. Casi siempre es la cadena de conexión, no el código.
Revisa en este orden:

1. Reemplazaste `USUARIO` y `PASSWORD` de verdad; no dejaste los placeholders.
2. La contraseña no tiene caracteres especiales sin codificar.
   - Lo más simple: crea un usuario nuevo en Atlas con una contraseña
     alfanumérica (por ejemplo `DevBlog2026Mongo`).
   - Si quieres conservar la contraseña, codifícala:

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
$env:MONGO_PASSWORD = "tu contraseña real"
.venv\Scripts\python.exe scripts\encode_mongo_password.py
```

Copia el resultado y úsalo en la URI, por ejemplo:

```text
mongodb+srv://devblog:MiPasswordCodificada@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

3. El usuario de Atlas está en el **mismo proyecto/clúster** y tiene permiso
   `readWriteAnyDatabase` o `Atlas admin`.
4. En **Network Access** está `0.0.0.0/0`.
5. En Render, el valor de `CMS_MONGO_URI` y `MONGO_URI` no tiene comillas,
   espacios al inicio/final ni saltos de línea. Pega solo la cadena.
6. Prueba la cadena desde tu laptop antes de volver a Render:

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
$env:CMS_MONGO_URI = "mongodb+srv://..."
.venv\Scripts\python.exe scripts\test_mongo_uri.py
```

El script te dice si el usuario, la red o la base son el problema. No imprime
la contraseña.

7. Si el script dice `Conexión correcta`, actualiza las dos variables en Render
   (`CMS_MONGO_URI` y `MONGO_URI`) y haz **Manual Deploy → Deploy latest commit**.

### Workaround temporal para presentar

Si necesitas el sitio funcionando ya y todavía no resuelves Atlas:

- **CMS**: elimina o deja vacía `CMS_MONGO_URI` en Render. El CMS usará SQLite
  en el disco efímero de Render; el seed cargará los tres artículos. Los
  artículos nuevos se perderán al reiniciar el servicio.
- **Métricas**: cambia `STORAGE` a `memory` y redespliega. GraphQL y el beacon
  funcionarán, pero los eventos se pierden al reiniciar.

Esto sirve para la demostración; la persistencia real se obtiene corrigiendo
la URI de Atlas.

**El CMS responde 502 al despertar.**
Render está arrancando; espera 30–60 s y recarga.

**`MONGO_URI` inválida o timeout.**
Revisa usuario/contraseña, `0.0.0.0/0` en Network Access y que la cadena incluya
`mongodb+srv://`.

**CORS en el navegador.**
Agrega el origen exacto (`https://mi-blog-dev.vercel.app` o
`https://leonardo251207.github.io`) a `CMS_CORS_ORIGINS` y `CORS_ORIGINS`.

**La consola no acepta el token.**
Usa el `CMS_CONSOLE_TOKEN` generado en el panel de Render, no el token local
`console-dev-token`.

**No aparecen publicaciones en la portada.**
Comprueba que `api-config.js` apunte a las URLs de Render y que el CMS tenga
artículos publicados.
