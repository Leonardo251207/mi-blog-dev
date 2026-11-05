# Despliegue concreto: GitHub Pages, Vercel y EC2

> Supuesto: el colector corre en una instancia EC2 con HTTPS, y observas tres proyectos
> independientes: uno en GitHub Pages, uno en `*.vercel.app` y uno servido desde EC2. Cada uno
> es una propiedad distinta, con sus claves y su ciclo de verificación.

---

## 1. Topología

```
Navegador ──beacon──┐
                    ├──► Colector (EC2, HTTPS) ──► MongoDB
Edge/logs ──────────┘
```

- **Beacon**: lo instala el navegador. Ve personas.
- **Edge**: lo instala el servidor o el proxy. Ve todas las peticiones, incluidos bots.

Cada sitio tendrá los canales que su plataforma permita:

| Sitio | Host típico | Estabilidad | Beacon | Edge / logs | Verificación |
|-------|-------------|-------------|--------|-------------|--------------|
| `pages` | `usuario.github.io/repo` | estable | Sí | No (nativo) | Meta tag |
| `vercel` | `proyecto.vercel.app` + previews | variable | Sí | Sí (middleware / log drain) | Well-known en el dominio estable |
| `ec2` | dominio propio | estable | Sí | Sí (nginx) | DNS TXT |

El host no identifica la propiedad: el `slug` sí. En Vercel los previews cambian de host en
cada despliegue; se etiquetan `entorno=preview` y no se verifican uno a uno.

---

## 2. Nomenclatura y claves

Tres proyectos, no uno. Cada uno es una propiedad distinta y se compara por separado. El host
puede cambiar; el `slug` no.

| Clave | Tipo | Dónde vive | Permiso |
|-------|------|------------|---------|
| `pk_pages_...` | Pública | HTML de GitHub Pages | Escribir eventos de `pages` |
| `pk_vercel_...` | Pública | HTML de Vercel | Escribir eventos de `vercel` |
| `sk_vercel_...` | Secreta | Variable de entorno de Vercel | Escribir visitas de edge |
| `pk_ec2_...` | Pública | Plantilla HTML de EC2 | Escribir eventos de `ec2` |
| `sk_ec2_...` | Secreta | Servicio de logs de EC2 | Escribir visitas de edge |

Regla: **la clave pública nunca autoriza lectura ni creación de sitios fuera de su lista de
orígenes. La clave secreta nunca llega al navegador.**

Los tres son proyectos independientes: cada uno es una propiedad con su propio ciclo, sus
claves y sus verificaciones. No se agrupan ni se comparan por defecto.

Si algún día quieres comparar el mismo contenido desplegado en varios hostings, añade una
etiqueta común (`proyecto: mi-blog`) y una dimensión `despliegue` (`pages`, `vercel`, `ec2`).
Hoy no hace falta.

---

## 3. GitHub Pages (nativo)

### 3.1 Instalar el beacon

- **Jekyll:** una sola vez en `_includes/head.html` o `_layouts/default.html`.
- **HTML plano:** en el `<head>` de cada página, o en la plantilla que uses para generarlas.

```html
<script
  defer
  src="https://metrics.tudominio.com/v1/beacon.js"
  data-key="pk_pages_..."
  data-site="pages"
  data-env="production"
></script>
```

### 3.2 Verificación

GitHub Pages no te deja publicar en la raíz del dominio si es un *project page*
(`usuario.github.io/repo/`). El archivo `/.well-known/` pertenece al sitio de usuario, no al
proyecto. Por eso:

- **Project page:** verifica con **meta tag** en el `<head>`.
- **User/org page o dominio propio:** puedes usar el archivo well-known en la raíz.

### 3.3 Orígenes y CORS

El origen es `https://usuario.github.io` para todos los project pages. Si tienes varios
proyectos bajo el mismo usuario:

- Usa una clave por proyecto.
- Añade `pathPrefix` al canal (`/repo-a/`, `/repo-b/`) para que el colector sepa a qué sitio
  pertenece cada evento.
- No confíes solo en el origen: el prefijo de ruta es lo que separa proyectos.

### 3.4 Bots

Nativos: **ninguno**. No hay servidor. Si los necesitas:

- Cloudflare delante con proxy activado y logs.
- O mover el sitio a Vercel/EC2.

No lo intentes con un script: los bots no ejecutan JavaScript.

---

## 4. Vercel (`*.vercel.app`)

### 4.1 Instalar el beacon

- **Next.js App Router:** en `app/layout.tsx`.
- **Next.js Pages Router:** en `pages/_document.tsx`.
- **Sitio estático:** en `index.html` o en la plantilla.

La clave va en una variable pública del proyecto:

```dotenv
NEXT_PUBLIC_METRICS_KEY=pk_vercel_...
NEXT_PUBLIC_METRICS_ENDPOINT=https://metrics.tudominio.com
```

### 4.2 Separar producción de preview

Cada despliegue de preview tiene una URL distinta (`proyecto-git-rama-equipo.vercel.app`).
Si no lo controlas, vas a contaminar las métricas de producción con tráfico de pruebas.

Dos opciones:

1. **No cargar el snippet fuera de producción.** En el layout:
   `if (process.env.VERCEL_ENV === 'production')`.
2. **Cargarlo etiquetado** con `data-env="preview"` y filtrar por esa dimensión en los reportes.

Recomendación: opción 1. Menos ruido y menos riesgo de exponer datos de pruebas.

Si eliges la opción 2, el colector registra cada host nuevo como `DominioDePropiedad` de tipo
`PREVIEW` y `entorno=preview`. No se verifica ni se marca canónico; se excluye de los reportes
por defecto. El `slug` de la propiedad no cambia aunque el host cambie.

### 4.3 Bots con middleware

El middleware se ejecuta en cada petición. Para no pagar cómputo en estáticos ni en assets:

- Limita con `matcher` a rutas HTML.
- Envía la visita con `waitUntil` para no bloquear la respuesta.
- Muestrea si el tráfico es alto (por ejemplo, 1 de cada 10).
- Usa la clave **secreta** `sk_vercel_`, nunca la pública.

Qué enviar por visita: ruta, método, estado, user-agent, país, `x-forwarded-for` (hasheada en
el colector), bytes si están disponibles y un identificador de petición para deduplicar.

### 4.4 Alternativa: log drain

Si tu plan lo permite, un log drain evita tocar el middleware. Vercel envía los logs a un
destino y tú los normalizas. Menos código, pero más dependencia del plan.

### 4.5 Verificación

`public/.well-known/metrics-verify.txt` funciona en el dominio del despliegue. Para producción
con dominio propio, DNS TXT es más robusto.

---

## 5. EC2

Es el caso completo: controlas HTML y servidor.

### 5.1 Beacon

El script va en la plantilla que renderiza el HTML (o en el `<head>` si es estático).

### 5.2 Bots desde nginx

Formato de log con lo que el colector necesita:

```
log_format metrics '$remote_addr - $remote_user [$time_local] '
                   '"$request" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent" '
                   '$request_time $upstream_response_time';

access_log /var/log/nginx/access.log metrics;
```

Envío al colector con **Vector**, **Fluent Bit** o un agente propio:

```
nginx access.log ──► Vector ──► POST /v1/collect/edge ──► Colector
```

- Lotes de 200–500 líneas.
- Reintento con backoff.
- Clave secreta `sk_ec2_` en variable de entorno o secreto montado.
- Si hay ALB o CloudFront delante, usa sus logs y añade `X-Request-Id` para deduplicar.

### 5.3 Qué añadir al log

- `request_time` y `upstream_response_time` para latencia.
- `$body_bytes_sent` para egress.
- `$status` para detectar 404/410 de bots.
- `X-Forwarded-For` si hay proxy delante.
- Un identificador de petición si puedes generarlo.

### 5.4 Verificación

DNS TXT en Route 53 (o en tu proveedor) es el método natural. También sirve el archivo
well-known servido por nginx.

---

## 6. El colector

### 6.1 Rutas

| Ruta | Quién la usa | Clave |
|------|--------------|-------|
| `/v1/beacon.js` | Navegadores | Ninguna (es público) |
| `/v1/collect` | Navegadores | `pk_...` pública |
| `/v1/collect/edge` | Vercel, EC2 | `sk_...` secreta o mTLS |
| `/v1/query` | Consumidores internos | Clave de API con scopes |
| `/v1/query` (doctor) | Instalación | Clave de lectura |

### 6.2 CORS

- Permitir los orígenes según el modo del canal: `EXACTO` (lista), `PATRON` (`*.vercel.app`,
  `*.github.io`) o `ABIERTO_CON_CUOTA` (previews y laboratorio).
- `https://usuario.github.io` con `pathPrefix` por proyecto.
- `https://proyecto.vercel.app` y sus previews, etiquetados y con cuota baja.
- `https://blog.ejemplo.com`.

No uses `*` como comodín global: un patrón explícito y una cuota son la barrera barata. La
clave es pública; el origen y la verificación son lo que separa datos legítimos de ruido.

### 6.3 Límites

- Tamaño máximo de lote por petición.
- Eventos por segundo por clave y por IP.
- Rechazo explícito (`429`) con `Retry-After`.
- Deduplicación por `eventId` (beacon) o `requestId` (edge).

---

## 7. Separar entornos

Una dimensión `entorno` (`production`, `preview`, `local`) en cada evento evita mezclar
pruebas con realidad. Los reportes la excluyen por defecto.

Alternativa más estricta: un sitio por entorno. Más limpio, más configuración.

---

## 8. Orden de trabajo recomendado

1. **Colector en EC2** con HTTPS, MongoDB y una clave de administración.
2. **Sitio GitHub Pages**: beacon + meta tag. Es el más rápido de validar.
3. **Sitio Vercel**: beacon en el layout, sin previews. Después middleware.
4. **Sitio EC2**: beacon + nginx → Vector → colector. Aquí llegan los bots.
5. **Alerta de ausencia de señal**: Telegram o Discord. Valida la instalación.
6. **Comparar**: misma ventana temporal, misma métrica, por sitio y por canal.

---

## 9. Checklist

- [ ] Colector accesible por HTTPS desde los tres orígenes.
- [ ] Tres propiedades creadas, cada una con sus dominios.
- [ ] Claves públicas por propiedad y secretas para edge.
- [ ] Verificación por dominio: meta en Pages, well-known en Vercel, DNS en EC2.
- [ ] Dominios de preview etiquetados como `PREVIEW` y excluidos por defecto.
- [ ] CORS según el modo de origen (`EXACTO`, `PATRON`, `ABIERTO_CON_CUOTA`).
- [ ] Beacon en producción, desactivado en previews.
- [ ] Vector enviando logs de nginx.
- [ ] Middleware de Vercel con `waitUntil` y muestreo.
- [ ] Panel de cobertura: Pages solo beacon; Vercel y EC2 beacon + edge.
- [ ] Alerta de "sin señal" configurada en Telegram o Discord.
- [ ] GA4, Search Console y AdSense sin configurar hasta tener cuenta real.
