# Instalación por snippet: una etiqueta y el sitio queda observado

> El objetivo: pegar tres líneas en el HTML y empezar a recibir datos. Sin SDK, sin build,
> sin registrar el sitio a mano. Con controles para que "automático" no signifique "cualquiera
> puede escribir en tu analytics".

---

## 1. El snippet

```html
<script
  defer
  src="https://metrics.tudominio.com/v1/beacon.js"
  data-key="pk_live_7f3a9c..."
  data-site="auto"
></script>
```

Eso es todo. `defer` evita bloquear el render. El script se sirve desde la propia API, así que
no hay paquete npm ni paso de compilación.

Con un sitio ya registrado, se cambia `data-site="auto"` por `data-site="blog"`.

### Atributos

| Atributo | Por defecto | Para qué |
|----------|-------------|----------|
| `data-key` | — | Clave pública de escritura |
| `data-site` | `auto` | Slug del sitio o `auto` para provisionar |
| `data-endpoint` | el del `src` | Colector alternativo |
| `data-sample` | `1` | Muestreo (0..1) para sitios de mucho tráfico |
| `data-spa` | `true` | Detectar cambios de ruta en aplicaciones de una página |
| `data-dnt` | `true` | Respetar Do Not Track / Global Privacy Control |
| `data-debug` | `false` | Registro en consola para diagnosticar |

---

## 2. Qué captura y qué no

**Captura:**

- `pageview` al cargar y en cada cambio de ruta (pushState, replaceState, popstate).
- Tiempo de permanencia y visibilidad (`visibilitychange`, `pagehide`).
- Web vitals: LCP, CLS, INP.
- Referrer, UTM, dispositivo, idioma, resolución.
- Clics salientes y descargas, si se habilitan.
- Errores de JavaScript, si se habilitan.

**No captura:**

- **Bots.** No ejecutan JavaScript. Para eso hace falta edge o logs, no snippet.
- Errores de servidor, estados HTTP ni bytes.
- Datos de GA4, anuncios o Search Console: esos llegan por sus APIs.
- Identidad entre sitios ni entre sesiones largas: sin cookies, no hay seguimiento persistente.

Esto último es deliberado: el snippet mide, no espía.

---

## 3. Los dos modos de registro

### Modo A — Sitio registrado (recomendado)

1. Se crea el sitio y el canal beacon por API o por bootstrap.
2. El sistema devuelve una clave pública `pk_...` ligada a la propiedad, con un modo de origen.
3. Se pega el snippet con `data-site="blog"`.

Ventaja: control total, sin estados intermedios. Coste: un paso previo.

### Modo B — Auto-provisión (el "pegás y funciona")

1. El operador crea una **clave de provisión** con un modo de origen (`EXACTO`, `PATRON` o
   `ABIERTO_CON_CUOTA`) y una lista de patrones (`*.github.io`, `*.vercel.app`, `midominio.com`).
2. El snippet usa `data-site="auto"` y esa clave.
3. En la primera petición, el colector:
   - valida la clave y el patrón de origen;
   - deriva la propiedad del hostname y le asigna un `slug` provisional;
   - registra el `host` como **`DominioDePropiedad` en estado `PENDIENTE`**;
   - crea la propiedad en estado **`PROVISIONAL`**;
   - responde con `siteId` y `estado`.
4. El sitio ya recibe datos, pero queda marcado como no verificado.

Si el host es un preview (`proyecto-git-rama.vercel.app`), se registra con
`tipo=PREVIEW` y `entorno=preview`. No se verifica: se acepta con cuota baja y se filtra en
los reportes. El `slug` se puede renombrar después; el histórico no se pierde porque los
eventos guardan el host.

Ventaja: cero fricción. Coste: hay que verificar para evitar suplantación.

### Por qué `PROVISIONAL` y no `ACTIVO` directamente

Una clave pública es visible para cualquiera. Si alguien la copia y la pega en su sitio, podría
inyectar datos en tu propiedad. La marca de provisional:

- aísla esos datos de los agregados principales;
- limita la tasa por clave y por origen;
- obliga a una verificación para promocionar el sitio;
- permite borrar lo provisional sin tocar datos legítimos.

---

## 4. Verificación de dominio

Tres métodos, del más simple al más robusto:

| Método | Cómo | Cuándo |
|--------|------|--------|
| **Meta tag** | `<meta name="metrics-site" content="token">` | HTML que controlas |
| **Archivo well-known** | `/.well-known/metrics-verify.txt` | Cualquier hosting estático |
| **DNS TXT** | `_metrics.midominio.com TXT "token"` | Cuando controlas el DNS |

El token se genera al registrar un dominio y caduca. Verificar promociona el **dominio** a
`VERIFICADO`; si es el primero, la propiedad pasa a `VERIFICADO` y entra en reportes normales.

La verificación es por dominio porque el host cambia. Un preview efímero puede quedarse en
`PENDIENTE` indefinidamente: no se puede verificar lo que dura horas. La propiedad se considera
verificada en cuanto un dominio estable lo está.

En GitHub Pages y Vercel el método natural es el archivo well-known o el meta tag. En AWS con
Route 53, el TXT es trivial.

---

## 5. Seguridad de una clave pública

La clave del snippet **no es un secreto**. Cualquiera puede leerla en el HTML. Por eso:

- Es **solo de escritura**: no permite consultar nada.
- Está **ligada a un modo de origen**: exacto, patrón o abierto con cuota. El colector compara
  el header `Origin` con ese modo.
- Tiene **cuota por sitio, por clave y por IP**.
- No puede crear sitios fuera del patrón de dominios de la clave de provisión.
- Los eventos de sitios provisionales se marcan y se separan.

Lo que **no** protege: un cliente que no sea un navegador puede falsificar el `Origin`. Por eso
la verificación de dominio es lo que separa "datos de mi sitio" de "datos de cualquiera". El
snippet reduce la fricción; la verificación pone el límite.

---

## 6. Plataforma por plataforma

### GitHub Pages

- Añadir el snippet en el `<head>` del layout o de cada página.
- Con Jekyll: en `_includes/head.html`, una sola vez.
- Es estático: **solo personas**. Sin proxy (Cloudflare) no hay bots.
- El archivo well-known se sirve desde la raíz del repo.

### Vercel

- Next.js: en `app/layout.tsx` o en `_document`, una vez.
- Sitio estático: en el `index.html`.
- Opcional: middleware o log drain para bots, además del snippet.
- El well-known va en `public/.well-known/`.

### AWS

- **S3 + CloudFront**: snippet en el HTML; logs de CloudFront a S3 para bots.
- **Amplify**: snippet en el layout; el resto igual.
- **EC2/ECS**: snippet en el HTML y logs del servidor para bots.

### Cualquier HTML

- Pegar antes de `</head>`. Nada más.

### Aplicaciones de una página (React, Vue, Astro, Svelte)

- `data-spa="true"` detecta cambios de ruta automáticamente.
- Si el router es exótico, una llamada manual: `window.metrics.pageview()`.
- Los web vitals se envían al ocultar la pestaña, no en cada ruta.

### Fallback sin JavaScript

Un `<noscript>` con un píxel de 1×1 permite registrar el pageview de humanos sin JS. No aporta
engagement ni web vitals. Es opcional y se puede desactivar.

---

## 7. Privacidad por defecto

- Sin cookies.
- Identificador de sesión en `sessionStorage`, rotativo y eliminado al cerrar la pestaña.
- Sin identificador persistente de visitante entre días.
- IP procesada en el servidor y almacenada solo como hash con sal rotativa.
- Ruta normalizada: se descartan parámetros y fragmentos.
- Do Not Track y Global Privacy Control respetados si `data-dnt="true"`.

---

## 8. Diagnóstico: el "doctor" del snippet

Un sitio recién instalado debe poder responderse solo:

- ¿La clave es válida?
- ¿El origen está permitido?
- ¿El sitio existe y en qué estado?
- ¿Llegó algún evento en los últimos minutos?
- ¿Qué canal falta para la métrica que buscas?

Eso se expone como una consulta de estado de instalación y como un comando de verificación.
El snippet con `data-debug="true"` lo imprime en consola.

Sin esto, el 90 % de los problemas de instalación se convierten en "no veo datos" y una tarde
perdida.

---

## 9. Qué añade esto al modelo

| Concepto | Cambio |
|----------|--------|
| `Propiedad` | Verificación `PROVISIONAL · VERIFICADO · RECHAZADO`; identidad por `slug` |
| `DominioDePropiedad` | Entidad nueva: host, tipo, estado y vigencia |
| `CanalDeCaptura` | Guarda clave pública, modo de origen, entornos y `pathPrefix` |
| `TokenDeVerificacion` | Entidad nueva: por dominio, método, valor, caducidad y fecha |
| Catálogo de métricas | El snippet solo habilita las métricas de beacon y `activa=true` |

---

## 10. Lo que el snippet no resuelve

- **Bots.** Sin edge o logs, invisibles.
- **Datos históricos.** Solo observa desde que se instala.
- **Atribución perfecta.** Adblockers, ITP y navegadores restrictivos pierden eventos. El
  sistema lo refleja en `completitud`, no lo esconde.
- **Verificación de propiedad.** Automatizar la instalación no verifica el dominio; eso es un
  paso aparte y deliberado.
