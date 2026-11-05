# Configuración: un `.env` para arrancar, no para modelar el negocio

> Objetivo: que un desarrollador clone el repo, copie `.env.example`, ejecute un comando y
> tenga el sistema funcionando. Sin magia y sin sorpresas.

---

## 1. El principio: tres niveles, no uno

Meter todo en `.env` parece simple hasta que tienes cinco sitios, tres integraciones y dos
entornos. Ahí el archivo se vuelve un jeroglífico con JSON escapado y secretos mezclados.

La separación sana es esta:

| Nivel | Qué configura | Dónde vive | Cambia cuándo |
|-------|---------------|------------|---------------|
| **0. Cero config** | Todo lo local con valores por defecto | `docker-compose.yml` | Nunca |
| **1. Despliegue** | Puertos, conexiones, modo, secretos, flags | `.env` | Al desplegar |
| **2. Estado inicial** | Sitios, canales y credenciales referenciadas | `config/bootstrap.yaml` | Al añadir un sitio |
| **3. Estado vivo** | Todo lo demás (sitios, canales, integraciones, reglas) | Base de datos, vía API | En caliente |

Regla: **el `.env` describe el proceso; la base de datos describe el negocio.** Si algo puede
cambiar sin reiniciar, no va en `.env`.

---

## 2. Nivel 0: cero configuración

```bash
git clone …
cd metrics-collector-retriever
cp .env.example .env
docker compose up
```

Con eso deberías tener:

- MongoDB arriba.
- Migraciones aplicadas.
- Catálogo de métricas sembrado.
- Un sitio de laboratorio, si `BOOTSTRAP_FILE` apunta al ejemplo.
- `/v1/query` y `/v1/collect` respondiendo.
- Una clave de administración impresa **una sola vez** en el log si no existía.

Nada de `npm install` en el front, porque no hay front. Nada de OAuth obligatorio, porque las
integraciones externas son opcionales.

---

## 3. Nivel 1: el contrato del `.env`

`.env.example` es documentación ejecutable: cada variable tiene un valor por defecto o un
comentario que explica cómo obtenerla.

| Variable | Por defecto | Para qué |
|----------|-------------|----------|
| `APP_ENV` | `local` | `local`, `staging`, `production` |
| `APP_MODE` | `minimal` | `minimal`, `standard`, `full` |
| `APP_PORT` | `8000` | Puerto de la API |
| `STORAGE` | `auto` | `auto`, `mongo` o `memory` |
| `MONGO_URI` | vacío | Conexión; si está vacío y `APP_ENV=local`, se usa Mongo en memoria |
| `MONGO_DB` | `metrics` | Base de datos |
| `ADMIN_API_KEY` | `dev-admin-key` | Cabecera `X-Admin-Key` de las mutaciones |
| `IP_HASH_SALT` | `dev-salt-change-me` | Pseudonimización de sesiones y visitantes |
| `CORS_ORIGINS` | `http://localhost:8000` | Orígenes permitidos, separados por coma |
| `CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Patrón para previews de Vercel |
| `BOOTSTRAP_FILE` | `config/bootstrap.yaml` | Estado inicial declarativo |
| `BOOTSTRAP_ON_START` | `true` | Aplicar el bootstrap al arrancar |
| `DEV_BEACON_KEY` | `pk_live_dev_…` | Clave pública del canal beacon de demo |
| `BEACON_RATE_LIMIT_PER_MINUTE` | `600` | Cuota básica por canal |

**Reservadas para fases siguientes.** `LOG_LEVEL`, `REDIS_URL`, las credenciales de GA4,
Search Console y AdSense, los flags de exportación/stream y las variables de alertas aún no se
leen en F1. Se documentan aquí para no cambiar el contrato cuando lleguen sus módulos.

**Modos de despliegue**, para que "solo el `.env`" sea verdad:

| Modo | Qué levanta | Variables mínimas |
|------|-------------|-------------------|
| `minimal` | API + Mongo, sin Redis ni workers | `MONGO_URI` |
| `standard` | + Redis, workers (rollup, sync, alertas) y agregados programados | `MONGO_URI`, `REDIS_URL` |
| `full` | + exportaciones, stream y alertas; policy bundle inactivo | las anteriores + flags |

El modo implica valores por defecto; una variable explícita siempre gana. Así un desarrollador
puede empezar con **una sola variable** y crecer sin reescribir nada.

En F1, `STORAGE=auto` significa: si hay `MONGO_URI`, usa MongoDB real; si no, y `APP_ENV` es
`local` o `test`, usa `mongomock-motor` en memoria para que el primer arranque no dependa de
Docker. En producción, `auto` exige `MONGO_URI` o `STORAGE=mongo` y falla si no está configurado.

**Integraciones externas: apagadas por defecto.** Hoy no hay cuenta de GA4, Search Console ni
AdSense. Las variables `*_CREDENTIALS_FILE` vacías dejan esas integraciones en
`DESHABILITADA`; sus métricas se declaran `activa=false` y se devuelven como no observables.
No se configura nada hasta que exista una cuenta real.

**Alertas: opcionales.** `ENABLE_ALERTS=false` por defecto. Cuando se active F4, se configura
un destino (Telegram, Discord o webhook) y se prueba con `probarNotificacion`.

---

## 4. Nivel 2: bootstrap declarativo

El `.env` no es sitio para listas anidadas. Para eso hay un archivo pequeño, versionable y
legible, al que el `.env` apunta:

```yaml
# config/bootstrap.yaml
sites:
  - slug: pages
    name: GitHub Pages
    type: propia
    timezone: Europe/Madrid
    retention_events_days: 90
    retention_aggregates_months: 25
    domains:
      - host: usuario.github.io
        type: plataforma
        environment: production
        canonical: true
    channels:
      - type: beacon
        origin_mode: pattern
        origins: ["https://usuario.github.io"]
        path_prefix: /repo/

  - slug: vercel
    name: Vercel
    type: propia
    timezone: Europe/Madrid
    domains:
      - host: proyecto.vercel.app
        type: plataforma
        environment: production
        canonical: true
    channels:
      - type: beacon
        origin_mode: pattern
        origins: ["https://proyecto.vercel.app", "https://*.vercel.app"]
        environments: ["production", "preview"]
      - type: edge
        secret_ref: env:VERCEL_EDGE_KEY
        environments: ["production"]

  - slug: lab
    name: Laboratorio
    type: laboratorio
    timezone: UTC
    domains:
      - host: localhost:3000
        type: temporal
        environment: local
        canonical: true
    channels:
      - type: beacon
        origin_mode: exact
        origins: ["http://localhost:3000"]
```

Los hosts de preview de Vercel no se declaran uno a uno: se registran solos como `PREVIEW`
cuando envían datos y se filtran por `environment`. Un dominio se retira, no se borra.

En F1, el canal beacon del sitio de demo usa `key_ref: env:DEV_BEACON_KEY` para que la clave
pública venga del `.env`. La auto-provisión de previews y las claves de edge (`secret_ref`)
quedan para los siguientes cortes; el bootstrap actual solo consume `key_ref` en canales beacon.

Las claves de edge se referencian por nombre (`secret_ref`), nunca se escriben en el YAML.

Reglas del bootstrap:

- **Idempotente.** Se aplica por `slug`; ejecutarlo dos veces no duplica nada.
- **No destructivo.** Nunca borra sitios ni mediciones. Si algo desaparece del archivo, se
  marca como no declarado, no se elimina.
- **Reconciliable.** Compara el estado declarado con el real y reporta diferencias.
- **Opcional.** Sin archivo, el sistema arranca vacío y se configura por API.
- **Reemplazable.** Lo que se crea por API no se pisa al reiniciar, salvo que el archivo lo
  declare explícitamente.

Equivalente por API para quien prefiera no tocar archivos: crear sitio y canales con comandos
de la superficie de consulta. El archivo es comodidad, no requisito.

---

## 5. Nivel 3: estado vivo

Sitios nuevos, canales, credenciales rotadas, agentes, reglas de precio y vistas guardadas se
gestionan por la API y viven en MongoDB. No requieren reinicio ni redeploy.

Esto es lo que evita que el `.env` se convierta en una base de datos disfrazada.

---

## 6. Secretos: el mismo contrato, distinto almacén

La aplicación lee siempre de la misma interfaz; el origen cambia por entorno:

| Entorno | Origen del secreto |
|---------|--------------------|
| Local | `.env` (nunca commiteado) |
| Contenedor | `.env` o Docker secrets |
| Producción | Gestor de secretos (Vault, AWS Secrets Manager, etc.) |

Convención `*_FILE`: si existe `MONGO_URI_FILE`, se lee el valor del archivo indicado. Así
funciona igual con variables que con secretos montados, sin cambiar código.

Reglas:

- `.env` va en `.gitignore`; `.env.example` sí se versiona.
- Los secretos se registran siempre redactados en logs y en el resumen de arranque.
- Rotar `IP_HASH_SALT` rompe la continuidad de visitantes únicos: se rota por política, no por
  comodidad.

---

## 7. Validación al arranque

Un `.env` mal puesto debe fallar **al inicio y con un mensaje útil**, no tres horas después
con un error de conexión.

- Validación tipada de todas las variables, con valores por defecto.
- Mensaje del tipo: `falta REDIS_URL y APP_MODE=standard; usa minimal o define REDIS_URL`.
- Resumen de arranque con la configuración efectiva, secretos redactados.
- Comando `config check` para validar sin arrancar.
- Endpoint de diagnóstico que dice qué superficies están activas y qué integraciones faltan.

---

## 8. Lo que no puede ir en `.env` (y por qué)

- **Credenciales OAuth interactivas.** AdSense y Search Console requieren un consentimiento
  en navegador una vez. Ese token se guarda cifrado y se referencia; no se escribe a mano.
- **Sitios y canales que cambian en caliente.** Van a la base de datos.
- **Dominios concretos.** Cambian (sobre todo en Vercel) y viven en la base de datos. El
  `.env` no fija ningún host.
- **Claves públicas de cada sitio.** Las genera el sistema al crear el canal; se copian al
  snippet, no al `.env`.
- **Tokens de bot y URLs de webhook.** Son secretos: `.env` en local, gestor de secretos en
  producción. Nunca se commitean.
- **Listas anidadas complejas.** Un YAML aparte es más legible y versionable.

Meter todo eso en `.env` no lo hace más fácil: lo hace más frágil.

---

## 9. El recorrido del desarrollador

```bash
cp .env.example .env      # 1. copiar
docker compose up         # 2. arrancar
curl localhost:8000/health # 3. comprobar
```

Para añadir un sitio:

1. Editar `config/bootstrap.yaml` (o crear el sitio por API).
2. Reiniciar, o ejecutar el comando de reconciliación.
3. Copiar el snippet del canal beacon que devuelve el sistema.
4. Verificar un dominio cuando quieras promocionar la propiedad de `PROVISIONAL` a `VERIFICADO`.

Para alertas (F4):

1. Crear el bot de Telegram o el webhook de Discord.
2. Poner el secreto en `.env`.
3. Activar `ENABLE_ALERTS=true`.
4. Probar con `probarNotificacion` y crear la primera regla.

Tres pasos para observar, cuatro para alertar. Sin variables ocultas y sin tocar la base de
datos a mano.
