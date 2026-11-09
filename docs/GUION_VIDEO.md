# Guion del video — DevBlog_

**Proyecto:** CMS API-First + blog estático + landing editable + publicidad + métricas con GraphQL + generador de HTML  
**Autor:** Leonardo Nucamendi Ruiz  
**Duración objetivo:** 14–16 minutos  
**Formato:** video grabación de pantalla + cámara al inicio y al cierre  
**Destino:** YouTube (puede ser "No listado" si el profe solo necesita el enlace)

---

## 1. Ficha rápida del video

| Dato | Valor |
|---|---|
| Título sugerido | DevBlog_ — CMS API-First, blog, landing, publicidad, métricas y generador estático |
| Duración ideal | 14–16 min (versión corta de 6–7 min al final) |
| Resolución | 1920×1080, 30 o 60 fps |
| Herramienta | OBS Studio (pantalla + micrófono) |
| Tono | Explicativo, en primera persona, sin leer demasiado |
| Idea central | "No hice solo una página: hice un CMS que administra el blog, la landing y la publicidad, y lo llevé a producción" |

### Enlaces que debes tener abiertos

| Recurso | URL |
|---|---|
| Blog local | http://127.0.0.1:5500/ |
| Consola local | http://127.0.0.1:5500/admin.html |
| Landing pública (API) | http://127.0.0.1:8080/api/v1/landing |
| Swagger CMS local | http://127.0.0.1:8080/docs |
| GraphiQL local | http://127.0.0.1:8000/v1/query |
| Swagger generador local | http://127.0.0.1:8001/docs |
| Blog en Vercel | https://mi-blog-dev.vercel.app/ |
| Blog en GitHub Pages | https://leonardo251207.github.io/mi-blog-dev/ |
| CMS en Render | https://devblog-cms-leonardo.onrender.com/docs |
| Métricas en Render | https://devblog-metrics-leonardo.onrender.com/v1/query |
| Generador en Render | https://devblog-generator-leonardo.onrender.com/docs |

**Token local de la consola:** `console-dev-token`  
**Token público local:** `public-dev-token`

> Importante: en el video **no muestres** la cadena de MongoDB Atlas, el `CMS_CONSOLE_TOKEN` de producción ni datos personales. El token local sí puedes mostrarlo porque es de desarrollo.

---

## 2. Antes de grabar: checklist de 10 minutos

- [ ] Abre las tres URLs de Render (`/health`) unos 5 minutos antes para despertar los servicios gratuitos.
- [ ] Levanta todo en local con el acceso directo **Iniciar DevBlog** o con `.\start-all.ps1`.
- [ ] Verifica que respondan: 8080, 8000, 8001 y 5500.
- [ ] Ten abiertas las pestañas del blog, la consola, Swagger, GraphiQL y el generador.
- [ ] En la consola, revisa las pestañas **Blog**, **Landing y publicidad** y **Métricas** antes de grabar.
- [ ] Ten el token `console-dev-token` en el portapapeles (no lo escribas en vivo si puedes evitarlo).
- [ ] Prepara en el Bloc de notas el texto del artículo de demo para pegarlo y no perder tiempo escribiendo.
- [ ] Cierra pestañas personales, correo, WhatsApp y notificaciones.
- [ ] Pon el navegador al 110 % o 125 % de zoom para que se lea bien en el video.
- [ ] Graba en 1080p, con el micrófono cerca y en un cuarto silencioso.
- [ ] Haz una grabación de prueba de 20 segundos y escúchala antes de la toma buena.
- [ ] Ten un plan B: si Render no despierta, muestras la versión local y dices que el despliegue gratuito se duerme.

**Consejo:** graba por bloques (introducción, demo, IA, cierre) y únelos en el editor. Así no repites todo si te equivocas en una parte.

---

## 3. Mapa del video

| Tiempo | Escena | Qué se muestra |
|---|---|---|
| 0:00–0:45 | Apertura | Cámara / diapositiva con tu nombre |
| 0:45–2:00 | Problema y visión | Diapositiva o README |
| 2:00–3:30 | Arquitectura y stack | Diagrama del README |
| 3:30–5:15 | Demo del blog y la landing | Portada, artículo, respaldo y publicidad |
| 5:15–7:45 | CMS API | Swagger, endpoints, seguridad |
| 7:45–9:45 | Consola CMS | Blog, landing, publicidad y publicación |
| 9:45–11:00 | Métricas | Panel de la consola y GraphiQL con tráfico real |
| 11:00–11:50 | Generador estático | Botón y artefacto HTML |
| 11:50–13:00 | Pruebas y despliegue | Terminal, Vercel, Pages, Render |
| 13:00–14:30 | Cómo usé IA | Diapositiva o pantalla con ejemplos |
| 14:30–15:30 | Decisiones, límites y cierre | Cámara / diapositiva |

---

## 4. Guion escena por escena

### Escena 1 — Apertura (0:00–0:45)

**En pantalla:** cámara o diapositiva con:

> **DevBlog_**  
> CMS API-First + blog + métricas + generador estático  
> Leonardo Nucamendi Ruiz  
> Ingeniería en Tecnologías de la Información e Innovación Digital

**Narración:**

> Buen día, profesor. Mi nombre es Leonardo Nucamendi Ruiz y soy estudiante de Ingeniería en Tecnologías de la Información e Innovación Digital.
>
> En este video les voy a presentar **DevBlog_**, mi proyecto de Aplicaciones Web. No es solo un blog: es un ecosistema con una API de gestión de contenido, un blog estático, una landing editable, publicidad configurable, un servicio de métricas y un generador de HTML.
>
> Les voy a contar **qué construí, cómo lo construí, qué decisiones tomé, cómo usé la inteligencia artificial y qué aprendí** en el proceso.

**Tip:** sonríe, habla más lento de lo normal y no empieces leyendo. Mira a la cámara en esta parte.

---

### Escena 2 — El problema y la visión (0:45–2:00)

**En pantalla:** el README o una diapositiva con tres columnas: **Problema → Decisión → Resultado**.

**Narración:**

> El punto de partida fue una pregunta: ¿cómo se hace un blog que no dependa de editar HTML a mano?
>
> Si el contenido vive dentro del HTML, cualquier cambio obliga a tocar código, volver a subir el sitio y rezar para no romper nada. Yo quería un flujo más profesional: escribir en una consola, guardar como borrador, publicar, y que el blog público se actualice solo.
>
> Por eso decidí construir el proyecto **API-First**. Eso significa que primero definí el contrato de la API —las rutas, los datos, los errores y los permisos— y después construí el frontend y el backend por separado.
>
> También me puse restricciones reales: tenía que funcionar en una laptop con Windows, sin Docker, con servicios gratuitos y con tiempo limitado. Esas restricciones guiaron casi todas mis decisiones técnicas.
>
> El resultado es un sistema con cuatro piezas: el **CMS**, el **blog + landing**, las **métricas** y el **generador estático**. La consola administra el blog, el contenido de la portada y el diseño de la publicidad. Cada pieza se puede probar por separado, pero trabajan juntas.

**Frase clave para memorizar:**  
> "Primero el contrato, después el código. Eso me permitió cambiar el frontend sin reescribir el backend."

---

### Escena 3 — Arquitectura y stack (2:00–3:30)

**En pantalla:** abre el README y muestra el diagrama de arquitectura (o una diapositiva con el mismo flujo).

**Narración:**

> Aquí está la arquitectura. El blog es estático y vive en Vercel y en GitHub Pages. Cuando un usuario entra, el navegador le pide los artículos al CMS, que corre en Render con FastAPI. El CMS guarda todo en MongoDB Atlas.
>
> En paralelo, el blog carga un pequeño beacon del servicio de métricas. Ese beacon registra la visita y la envía al colector, que también guarda en MongoDB. Las consultas de tráfico se hacen con GraphQL.
>
> Y la consola de administración habla con el CMS para crear y publicar artículos, editar la landing y diseñar la publicidad, y con el generador cuando quiero convertir un artículo en HTML estático. El resumen de métricas también lo pide a la API del CMS, y el CMS consulta GraphQL por dentro: así el navegador no necesita permisos extra de CORS.
>
> En local uso cuatro puertos para que nada choque: **CMS en 8080, métricas en 8000, generador en 8001 y blog en 5500**.
>
> El stack es Python 3.12 con FastAPI y Pydantic en el backend; JavaScript vanilla en el frontend; SQLite en local y MongoDB en producción; y Render, Vercel, GitHub Pages y GitHub Actions para el despliegue.
>
> ¿Por qué FastAPI? Porque me da validación automática con Pydantic y documentación interactiva con Swagger sin escribirla a mano. ¿Por qué JavaScript vanilla? Porque quería demostrar que entiendo el DOM, `fetch`, `sessionStorage` y los eventos sin esconderlo detrás de un framework. Y ¿por qué SQLite y MongoDB? Porque SQLite me da persistencia local sin instalar nada, y MongoDB me da persistencia en la nube gratis.

**Tip:** no leas el diagrama completo; señala con el mouse las cuatro cajas mientras hablas.

---

### Escena 4 — Demo del blog (3:30–5:15)

**En pantalla:** `http://127.0.0.1:5500/`

**Narración:**

> Este es el blog. La portada tiene una presentación, mis tecnologías, proyectos destacados, certificaciones y la sección de notas.
>
> La presentación, los títulos de sección, los proyectos, las certificaciones y el contacto no están escritos en el HTML: vienen del documento de la landing que se administra en el CMS. Si borro un proyecto o cambio el tagline en la consola, la portada se actualiza cuando publico.
>
> También hay un espacio de **publicidad** que se puede activar, desactivar y rediseñar desde la consola sin tocar el HTML.
>
> Lo importante está en **Notas y experimentación**. Estos tres artículos no están escritos en el HTML: se están pidiendo al CMS en el puerto 8080. Si abro las herramientas de desarrollo y voy a la pestaña de red, van a ver la petición `GET /api/v1/posts`.
>
> Fíjense que la tarjeta muestra la categoría, el tiempo de lectura y la fecha. Esos datos vienen de la API, no están duplicados en el frontend.

**Acción:** abre una tarjeta.

> Al entrar a un artículo, el blog usa el slug de la URL para pedir el artículo completo. El contenido está en Markdown y se renderiza de forma segura. También se registra la vista con un `POST` al CMS.
>
> Si la API no responde, el blog no se queda en blanco: muestra tarjetas de respaldo con contenido estático. Eso lo hice a propósito para que la portada siga siendo útil aunque el backend esté dormido o falle.

**Acción:** muestra el enlace "Ver versión interactiva" si aparece.

> Algunos artículos tienen una versión interactiva original, y el artículo dinámico enlaza a ella. Así conservo el diseño que ya tenía sin perder la ventaja del CMS.

**Frase clave:**  
> "El blog no depende de que la API esté siempre viva: si falla, degrada la experiencia en lugar de romperse."

---

### Escena 5 — CMS API (5:15–7:45)

**En pantalla:** `http://127.0.0.1:8080/docs`

**Narración:**

> Este es el corazón del proyecto: el CMS. Está hecho con FastAPI y tiene **12 endpoints de blog** —seis para borradores y seis para publicaciones, incluyendo el registro de vistas— más **11 endpoints nuevos** para landing, publicidad y el resumen de métricas. Además tiene `/health` para saber si está vivo y `/docs` para la documentación interactiva.
>
> Los endpoints de contenido nuevo son: lectura pública de la landing, borrador y publicación de la landing, CRUD de publicidad y `GET /api/v1/metrics/overview`, que consulta el servicio de métricas desde el backend.
>
> El flujo es el de un CMS real: creo un borrador, lo edito, lo publico y entonces aparece en el blog. También puedo consultar por ID, consultar por slug, registrar vistas y eliminar una publicación.
>
> La autenticación es con **tokens Bearer** y scopes. La consola tiene permiso de escritura; el sitio público solo tiene permiso de lectura y de registrar vistas. El token de la consola nunca está en el código: se escribe en la interfaz y se guarda solo en `sessionStorage`. El token público sí está en el JavaScript porque el navegador lo necesita, pero es de solo lectura y tiene límite de peticiones.

**Acción opcional (muy recomendable):** en Swagger, haz un `GET /api/v1/posts` sin token y muestra el `401`. Luego autoriza con `public-dev-token` y muestra el `200`.

> Sin token, la API responde `401`. Con el token correcto, responde `200`. Todos los errores tienen el mismo formato para que el frontend sepa qué mostrar.

**Narración (decisiones técnicas):**

> Ahora les cuento las decisiones que más trabajo me dieron y por qué las tomé.
>
> **Uno: idempotencia.** Si el navegador reintenta un `POST` porque se cayó la conexión, no quiero que se cree el artículo dos veces. La API guarda la respuesta durante 24 horas, asociada al consumidor y a una `Idempotency-Key`. Si llega la misma petición, devuelve el mismo resultado en lugar de duplicar.
>
> **Dos: rate limit.** La consola puede hacer 60 peticiones por minuto y el sitio público 10 por segundo. Si se pasa, responde `429` con `Retry-After`. Eso protege la API de abuso y de bucles accidentales.
>
> **Tres: paginación con cursor firmado.** No uso números de página; uso un cursor opaco que va firmado con HMAC. Si alguien lo altera, la API responde `422 INVALID_CURSOR`. Así no se puede inventar una página solo porque el cursor parezca JSON válido.
>
> **Cuatro: caché.** Cada respuesta lleva `ETag` y `Cache-Control`. Si el contenido no cambió, la API responde `304` y no reenvía el cuerpo. Eso ahorra datos y hace el sitio más rápido.
>
> **Cinco: persistencia intercambiable.** El servicio no sabe si está usando SQLite o MongoDB. Hay una interfaz de repositorio y una fábrica que elige Mongo si existe `CMS_MONGO_URI`; si no, usa SQLite. Eso me permitió desarrollar local sin internet y desplegar en la nube sin reescribir la lógica.
>
> También uso UUIDv7 —que es ordenable por tiempo—, slug único, tiempo de lectura calculado y validaciones con Pydantic. La idea es que la API no sea solo un CRUD, sino un contrato confiable.

**Si quieres demostrar algo fuerte (opcional):**

1. En Swagger, `GET /api/v1/posts?limit=1`.
2. Copia el `next_cursor`.
3. Cámbiale un carácter.
4. Ejecuta de nuevo y muestra el `422 INVALID_CURSOR`.

> "Como ven, no basta con que el cursor parezca válido: tiene que tener la firma correcta."

---

### Escena 6 — Consola CMS: blog, landing y publicidad (7:45–9:45)

**En pantalla:** `http://127.0.0.1:5500/admin.html`

**Narración:**

> Esta es la consola de administración. Es la parte que convierte el CMS en algo usable sin tener que escribir peticiones a mano.
>
> Me conecto con el token de desarrollo. El token se guarda solo en esta pestaña; si cierro la pestaña, se pierde. No está escrito en el código.

**Acción:** escribe `console-dev-token` y da clic en **Conectar**.

> La consola tiene tres pestañas: **Blog**, **Landing y publicidad** y **Métricas**. En Blog veo los borradores y las publicaciones. Puedo crear un borrador nuevo, editarlo, guardarlo, publicarlo o eliminarlo. También puedo cargar más resultados, porque la lista está paginada.

**Acción:** pestaña **Blog** → **+ Nuevo borrador** y llena:
- Título: `Cómo preparé DevBlog_ para producción`
- Slug: se genera solo (puedes dejarlo)
- Etiquetas: `documentación, deployment`
- Contenido: pega un texto corto con un título, un párrafo, una lista y un bloque de código.

> El slug se genera a partir del título. Si ya existe, la API responde `SLUG_DUPLICATED` y tengo que cambiarlo. Esa validación también está en el servidor, no solo en la interfaz.

**Acción:** clic en **Vista previa**.

> La vista previa renderiza el Markdown antes de publicar. Así evito publicar algo con el formato roto.

**Acción:** **Guardar borrador** y luego **Publicar**.

> Al publicar, el CMS cambia el estado, genera la URL del artículo y lo saca de la lista de borradores. Si voy al blog, ya aparece la tarjeta nueva.

**Acción:** pestaña **Landing y publicidad**.

> Aquí está el cambio que pedí para esta entrega: la consola también administra la portada. Puedo editar el hero, los títulos de sección, las tecnologías, los proyectos, las certificaciones y el contacto. La landing tiene **borrador** y **versión publicada**: guardo sin romper lo que ya está en línea y publico cuando estoy conforme.

**Acción:** cambia el tagline, pulsa **Guardar borrador**, recarga el blog y muestra que todavía se ve el texto anterior. Después pulsa **Publicar landing**, recarga y muestra el texto nuevo.

> Esa separación es importante: el sitio público lee la copia publicada; la consola edita la copia de trabajo. Así puedo preparar un cambio con calma.

**Acción:** baja a **Diseño del anuncio** y cambia título, disposición y colores; guarda y recarga la portada.

> La publicidad es una entidad aparte. Tiene textos, llamada a la acción, imagen opcional, tres disposiciones —banner, split y tarjeta— y colores de fondo, texto y acento. El interruptor **activa** decide si aparece en el sitio. La consola muestra una vista previa en vivo antes de guardar.

**Frase clave:**  
> "La consola no es un adorno: es el flujo real de trabajo de un editor de contenidos, ahora también para la portada y la publicidad."

---

### Escena 7 — Métricas: consola y GraphQL (9:45–11:00)

**En pantalla:** consola, pestaña **Métricas**.

**Narración:**

> El cuarto componente es el servicio de métricas. El blog carga un beacon muy pequeño con `metrics.js`. Ese beacon envía la visita y el engagement al colector, sin bloquear la carga de la página.
>
> El servicio normaliza las rutas: por ejemplo, si la URL tiene un UUID o un número, lo convierte en `:id` para agrupar las visitas por tipo de página. También usa un hash con salt para no guardar la IP en claro; lo que se guarda es un identificador pseudónimo.

**Acción:** en la consola, pestaña **Métricas**, elige 7 días y granularidad por día; pulsa **Actualizar**.

> Esta pestaña muestra el resumen sin salir del CMS: pageviews, sesiones, visitantes únicos, rutas más vistas y la serie temporal. La consola no llama a GraphQL directamente desde el navegador: pide `GET /api/v1/metrics/overview` al CMS, y el CMS consulta el servicio de métricas. Si el servicio está dormido, el panel dice «Métricas no disponibles» y el resto de la consola sigue funcionando.

**Acción:** abre `http://127.0.0.1:8000/v1/query`.

> Para consultar el tráfico a detalle uso GraphQL. Esta es la consulta de los sitios:

**Acción:** ejecuta:

```graphql
{
  sitios {
    slug
    nombre
    estado
  }
}
```

> Aparece el sitio `devblog`. Ahora la consulta de tráfico:

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

> Aquí veo pageviews, sesiones, visitantes únicos estimados, las rutas más visitadas y los hosts. Estos datos salen de las visitas reales que acabo de hacer al blog, no de valores inventados.
>
> La ventaja de GraphQL es que el cliente pide exactamente los campos que necesita. No tengo que crear un endpoint distinto para cada vista del panel.

**Tip:** si los números salen en cero, visita el blog otra vez y recarga la consulta; el beacon tarda unos segundos.

---

### Escena 8 — Generador estático (11:00–11:50)

**En pantalla:** vuelve a la consola, abre un artículo y haz clic en **Generar HTML estático**.

**Narración:**

> El último servicio es el generador de sitios estáticos. La consola toma el título, el slug, las etiquetas y el Markdown del artículo, los convierte en bloques —encabezados, párrafos, código, citas e imágenes— y llama al generador.
>
> El generador devuelve un `page_id`, un estado, el motor que usó, un **checksum SHA-256** y la URL del artefacto. El checksum sirve para verificar que el HTML generado corresponde exactamente al contenido que se envió.
>
> Los artefactos se guardan en `dev-blog/generated/{slug}.html` y también se pueden servir desde el generador. La página dinámica sigue siendo la principal; el HTML estático es una copia de respaldo o un artefacto para publicar en otro lado.
>
> Es importante decir que el generador no tiene autenticación y su CORS es abierto: está pensado para demostración local. En un proyecto real habría que ponerlo detrás de un proxy o de una clave de API.

**Acción:** abre el enlace del artefacto generado.

> Aquí está el HTML generado. Es más simple que la página del blog, pero funciona sin depender del CMS.

---

### Escena 9 — Pruebas y despliegue (11:50–13:00)

**En pantalla:** terminal en el proyecto.

**Narración:**

> Un proyecto no está terminado cuando "se ve bien": está terminado cuando puedo demostrar que funciona. Por eso escribí pruebas automatizadas para los tres servicios.
>
> En total son **74 pruebas**: 57 del CMS, 13 de métricas y 4 del generador.

**Acción:** ejecuta las tres suites (puedes tenerlas previamente corridas y mostrar el resultado, o correrlas en vivo si tu laptop es rápida).

```powershell
cd API\devblog-cms-api-1.2\devblog-cms-api
.venv\Scripts\python.exe -m pytest -q

cd ..\..\..\pendiente\metrics-navigation-main\metrics-navigation-main
.venv\Scripts\python.exe -m pytest tests -q

cd ..\..\static-sites-generator-main\static-sites-generator-main
.venv\Scripts\python.exe -m unittest tests/test_api.py -v
```

> Las pruebas del CMS cubren el contrato completo, la persistencia entre reinicios, el cursor firmado, CORS, salud, el formato de errores, la landing con borrador/publicación, el CRUD de publicidad y el resumen de métricas. Las de métricas cubren el beacon y las consultas. Las del generador cubren la creación de páginas y la verificación de integridad.
>
> Para el despliegue usé la capa gratuita de Render con un blueprint, `render.yaml`, que declara los tres servicios. La base de datos es MongoDB Atlas M0, también gratuita. El blog está en Vercel y en GitHub Pages; GitHub Actions lo publica automáticamente.
>
> El archivo `api-config.js` detecta el hostname: si estoy en `localhost` usa los servicios locales; si estoy en Vercel o GitHub Pages usa las URLs de Render. Por eso el mismo código funciona en los dos entornos.
>
> La limitación del plan gratuito es que Render duerme los servicios sin tráfico. La primera petición puede tardar entre 30 y 60 segundos. Para una presentación hay que abrir las URLs unos minutos antes.

**Acción:** muestra Vercel y GitHub Pages funcionando. Si Render ya despertó, muestra la portada con las tarjetas reales.

> Como ven, la versión publicada no es una maqueta: está consumiendo el CMS real en Render.

---

### Escena 10 — Cómo usé la inteligencia artificial (13:00–14:30)

> **Nota para ti:** ajusta los ejemplos a lo que realmente hiciste. Lo importante es que cuentes la verdad y que se vea que usaste la IA con criterio, no que copiaste sin revisar. La versión de abajo es coherente con el repo.

**En pantalla:** una diapositiva con dos columnas: **"Lo que hizo la IA"** y **"Lo que hice yo"**.

**Narración:**

> Quiero ser transparente con cómo usé la inteligencia artificial, porque fue una herramienta importante, pero no fue la que tomó las decisiones.
>
> La usé como **copiloto**, no como piloto automático. La IA me ayudó a acelerar cuatro cosas:
>
> **Primera: convertir el contrato en tareas.** Le pasé la especificación de la API y le pedí que me ayudara a dividirla en módulos, a detectar casos borde y a proponer una estructura de carpetas. La decisión de qué arquitectura usar fue mía; la IA me ayudó a ordenar el trabajo.
>
> **Segunda: generar código repetitivo.** Los esquemas de Pydantic, los routers, los repositorios y los scripts de arranque tienen mucho patrón repetido. Le pedí borradores, los revisé, los adapté y los probé. No acepté código sin entenderlo.
>
> **Tercera: escribir pruebas.** Le pedí pruebas para los casos que más miedo me daban: cursor alterado, idempotencia, `401`, `429`, `304`, errores de validación y persistencia. Varias de esas pruebas encontraron diferencias entre lo que yo creía y lo que el código hacía.
>
> **Cuarta: depurar y documentar.** Cuando apareció un error de CORS con `navigator.sendBeacon`, o cuando MongoDB Atlas no autenticaba, la IA me ayudó a leer el error y a plantear hipótesis. También me ayudó a redactar el README y las guías de despliegue.
>
> Pero hay cosas que no delegué: **la definición del contrato, la elección de tecnologías, la configuración de Render y Atlas, la revisión de cada cambio, las pruebas en el navegador y las decisiones de diseño**. La IA proponía; yo verificaba.
>
> Un ejemplo concreto: la IA me propuso usar `uv` para crear los entornos, pero mi laptop no lo tenía. En lugar de forzar la instalación, hice que `setup.ps1` funcionara con `uv` si estaba y con `python -m venv` si no. Eso es adaptar la herramienta al contexto, no al revés.
>
> Otro ejemplo: en métricas, el beacon fallaba por CORS. La solución no era "poner `*` en todo"; era permitir credenciales y el origen correcto. Ese tipo de decisión requiere entender el problema, no solo copiar la respuesta.
>
> Mi conclusión es que la IA te ahorra tiempo en lo mecánico, pero **no te ahorra entender**. Si no sabes por qué funciona, no lo puedes defender.

**Frases clave para memorizar:**

> "La IA me ayudó a escribir más rápido; yo me hice responsable de que funcionara."
>
> "Usé la IA para explorar opciones, no para evitar decidir."

---

### Escena 11 — Decisiones, límites y cierre (14:30–15:30)

**En pantalla:** cámara o diapositiva con **"Qué aprendí"**.

**Narración:**

> Para cerrar, les comparto las decisiones que más me marcaron y los límites que soy consciente de que tiene el proyecto.
>
> **Decisiones que volvería a tomar:** definir el contrato antes de programar; separar la lógica de negocio del repositorio para poder cambiar SQLite por Mongo; escribir pruebas desde el inicio; y documentar el despliegue, porque el despliegue también es parte del proyecto.
>
> **Límites que reconozco:** el rate limit y la idempotencia viven en memoria por proceso, así que con varias instancias habría que moverlos a Redis. El generador no tiene autenticación y es solo para demostración. Los servicios gratuitos de Render se duermen. Y los artefactos del generador son efímeros.
>
> **Lo que aprendí:** que un proyecto web no es solo la pantalla; es la API, la base de datos, la seguridad, las pruebas, el despliegue y la documentación. Y que usar IA sin criterio es peligroso: te puede dar una respuesta que se ve bien pero que no entiendes.
>
> Este proyecto me dejó una frase que ahora uso siempre: **"si no lo puedo explicar, no lo puedo defender"**. Por eso hice este video explicando no solo qué hace, sino por qué lo hice así.
>
> Muchas gracias por su atención. Los enlaces al blog, al código y a la documentación están en la descripción del video.

**Cierre en cámara:** pausa de 2 segundos y corta.

---

## 5. Versión corta (6–7 minutos)

Úsala si el profe pidió un máximo de 7 minutos. Conserva solo esto:

| Tiempo | Contenido |
|---|---|
| 0:00–0:30 | Presentación y qué es DevBlog_ |
| 0:30–1:15 | Problema y solución API-First |
| 1:15–2:15 | Arquitectura y stack (diagrama) |
| 2:15–3:15 | Demo: blog + artículo |
| 3:15–4:00 | CMS: Swagger, tokens, idempotencia, cursor |
| 4:00–4:50 | Consola: blog, landing y publicidad |
| 4:50–5:40 | Métricas en la consola + GraphQL + generador |
| 5:40–6:20 | Pruebas (74) y despliegue |
| 6:20–7:00 | Cómo usé IA + cierre |

**Narración condensada:**

> DevBlog_ es un ecosistema de gestión de contenido: una API hecha con FastAPI, un blog estático, un servicio de métricas con GraphQL y un generador de HTML. El blog está en Vercel y GitHub Pages; la API y los servicios están en Render, con MongoDB Atlas.
>
> Lo construí API-First: primero definí el contrato de 12 endpoints de blog y después amplié con landing, publicidad y el resumen de métricas. Eso me permitió probar cada parte y cambiar el frontend sin reescribir la API.
>
> La API tiene tokens con scopes, idempotencia para no duplicar artículos, rate limit, paginación con cursor firmado y caché con ETag. En local usa SQLite; en producción, MongoDB.
>
> La consola permite crear, editar, previsualizar y publicar artículos; editar la landing con borrador y publicación; diseñar la publicidad; y ver el resumen de métricas. El blog consume la API y, si falla, muestra contenido de respaldo. Las métricas registran visitas reales y se consultan con GraphQL.
>
> Todo está probado con 74 pruebas automatizadas: 57 del CMS, 13 de métricas y 4 del generador. El despliegue es gratuito y automatizado, con la limitación de que Render se duerme sin tráfico.
>
> Usé IA como copiloto: para ordenar el contrato, generar código repetitivo, escribir pruebas y depurar errores. Pero las decisiones de arquitectura, la configuración, la revisión y las pruebas en el navegador fueron mías. La IA me ayudó a escribir más rápido; yo me hice responsable de que funcionara.
>
> Lo más valioso que aprendí es que un proyecto no termina en la pantalla: termina cuando está probado, desplegado y documentado. Gracias.

---

## 6. Datos que debes memorizar

| Concepto | Dato |
|---|---|
| Endpoints del CMS | 12 de blog + 11 de landing/publicidad/métricas (+ `/health` y `/docs`) |
| Borradores / publicaciones | 6 y 6 |
| Pruebas totales | 74 |
| Pruebas CMS | 57 (contrato, contenido y Mongo) |
| Pruebas métricas | 13 |
| Pruebas generador | 4 |
| Puertos locales | 8080 CMS, 8000 métricas, 8001 generador, 5500 blog |
| Tokens locales | `console-dev-token` (escritura), `public-dev-token` (lectura) |
| Rate limit | 60/min consola, 10/s público |
| Idempotencia | 24 horas (86,400 s), por consumidor y clave |
| Cursor | Opaco, firmado con HMAC; alterado → `422 INVALID_CURSOR` |
| Caché | `ETag` + `Cache-Control`; sin cambios → `304` |
| IDs | UUIDv7 |
| Base local | SQLite en `data/devblog.db` (posts, landing, ads) |
| Base producción | MongoDB Atlas M0 (512 MB) |
| Landing | Borrador + publicada; el sitio lee la publicada |
| Publicidad | Entidad aparte; solo se muestra si `active` |
| Métricas en consola | `GET /api/v1/metrics/overview` (backend → GraphQL) |
| Hosts | Render (3 servicios), Vercel y GitHub Pages |
| Cold start de Render | 30–60 s |
| Generador | `POST /api/v1/pages`, devuelve `checksum_sha256` |

---

## 7. Preguntas probables del profesor (y cómo responder)

**1. ¿Por qué elegiste API-First?**  
> Porque el contrato es la parte más estable del sistema. Si primero defino rutas, datos y errores, puedo construir el frontend y el backend en paralelo y cambiarlos sin romper el otro. Además, la API se puede reutilizar en otro proyecto.

**2. ¿Por qué FastAPI y no Express, Django o Laravel?**  
> Porque FastAPI me da validación con Pydantic, documentación Swagger automática y buen rendimiento con poco código. Python ya lo estaba usando en la carrera y me permitía integrar los servicios del ecosistema sin cambiar de lenguaje.

**3. ¿Cómo proteges la consola?**  
> Con un token Bearer de escritura que no está en el repositorio. Se escribe en la consola y se guarda solo en `sessionStorage`. En producción, Render genera el token y yo lo copio desde el panel. El token público es distinto, es de solo lectura y tiene rate limit.

**4. ¿Qué pasa si alguien altera el cursor de paginación?**  
> La API responde `422 INVALID_CURSOR`. El cursor lleva una firma HMAC; no basta con que sea JSON válido. Así evito que se inventen páginas o se salten registros.

**5. ¿Cómo evitas artículos duplicados si se reintenta una petición?**  
> Con idempotencia. El cliente manda una `Idempotency-Key`; la API guarda la respuesta 24 horas por consumidor y clave. Si llega la misma petición, devuelve el mismo resultado en lugar de crear otro artículo.

**6. ¿Qué pasa si Render se duerme?**  
> La primera petición tarda 30–60 segundos. Para la presentación abro las URLs antes. Si el CMS no responde, el blog muestra tarjetas de respaldo en lugar de quedarse vacío.

**7. ¿Cómo se conecta Vercel con Render?**  
> `api-config.js` detecta el hostname. En `localhost` usa `127.0.0.1`; en Vercel o GitHub Pages usa las URLs de Render. El CMS tiene CORS configurado con esos orígenes exactos.

**8. ¿Por qué usaste SQLite y MongoDB?**  
> SQLite para desarrollo local: cero configuración y persistencia en un archivo. MongoDB Atlas para producción: persistencia en la nube dentro de la capa gratuita. La lógica es la misma porque está detrás de una interfaz de repositorio.

**9. ¿Qué parte hizo la IA y qué parte tú?**  
> La IA me ayudó con borradores de código, pruebas, explicaciones de errores y documentación. Yo definí el contrato, elegí las tecnologías, configuré Render y Atlas, revisé cada cambio y probé todo en el navegador. La IA proponía; yo verificaba.

**10. ¿Cómo administras la landing y la publicidad?**  
> La landing es un documento JSON con dos copias: borrador y publicada. La consola edita el borrador y el sitio público lee la publicada. La publicidad es una entidad aparte con textos, imagen, llamada a la acción, tres disposiciones y colores; solo se muestra si está activa. Todo se guarda en la misma base que los posts.

**11. ¿Qué mejorarías si tuvieras más tiempo?**  
> Movería el rate limit y la idempotencia a Redis para soportar varias instancias; agregaría autenticación al generador; pondría pruebas end-to-end con el navegador; y agregaría un editor Markdown más completo en la consola.

**12. ¿Por qué no usaste Docker?**  
> Porque no estaba instalado en la máquina y el objetivo era que el proyecto corriera ya. Dejé los `Dockerfile` disponibles para un despliegue futuro, pero para local usé entornos virtuales separados, que era suficiente y más simple.

**13. ¿Cómo manejas los errores?**  
> Todos los errores tienen el mismo formato `{"error": {...}}`, con código, mensaje y detalles. Eso permite que la consola y el blog muestren mensajes claros sin adivinar qué falló.

---

## 8. Cómo contar la parte de IA (versión honesta y defendible)

Si el profe pregunta específicamente por la IA, usa esta estructura de tres pasos:

1. **Qué le pedí:** "Le pedí que me ayudara a dividir el contrato, generar código repetitivo, proponer pruebas y explicar errores."
2. **Qué hice con eso:** "Revisé, adapté, ejecuté las pruebas y probé en el navegador. No acepté nada sin entenderlo."
3. **Qué aprendí:** "La IA acelera lo mecánico, pero no reemplaza el criterio. Si no puedo explicar por qué funciona, no lo puedo defender."

**Tres ejemplos de prompts que puedes mencionar:**

> "Tengo este contrato de 12 endpoints. Ayúdame a dividirlo en módulos y a listar los casos borde antes de escribir código."

> "Genera pruebas para estos casos: cursor alterado, idempotencia, 401, 429, 304 y errores de validación. No implementes la solución todavía."

> "Este es el error de CORS con `navigator.sendBeacon`. Explícame por qué ocurre y dame dos opciones con ventajas y desventajas."

**Lo que no debes decir:** "La IA hizo todo." Eso le quita valor a tu trabajo y el profe lo va a notar. Tampoco digas "no usé IA" si sí la usaste: es mejor ser transparente y mostrar criterio.

---

## 9. Descripción para YouTube (copiar y pegar)

**Título:**

> DevBlog_ — CMS API-First, blog, landing, publicidad, métricas y generador | Leonardo Nucamendi Ruiz

**Descripción:**

> Presentación del proyecto DevBlog_, un ecosistema de gestión de contenido construido con FastAPI, MongoDB Atlas, Render, Vercel y GitHub Pages.
>
> Incluye:
> • CMS API con 12 endpoints de blog y 11 de landing, publicidad y métricas; tokens, idempotencia, rate limit y paginación con cursor firmado.
> • Blog estático que consume la API y tiene respaldo si el backend falla.
> • Landing editable desde la consola, con borrador y publicación separados.
> • Publicidad configurable: textos, imagen, llamada a la acción, disposición y colores.
> • Consola de administración con pestañas de Blog, Landing y Publicidad, y Métricas.
> • Métricas con beacon, consultas GraphQL y resumen dentro de la consola.
> • Generador de HTML estático con checksum SHA-256.
> • 74 pruebas automatizadas.
>
> Capítulos:
> 0:00 Introducción
> 0:45 Problema y visión
> 2:00 Arquitectura y stack
> 3:30 Demo del blog y la landing
> 5:15 CMS API
> 7:45 Consola: blog, landing y publicidad
> 9:45 Métricas en la consola y GraphQL
> 11:00 Generador estático
> 11:50 Pruebas y despliegue
> 13:00 Cómo usé la inteligencia artificial
> 14:30 Decisiones, límites y cierre
>
> Blog: https://mi-blog-dev.vercel.app/
> GitHub Pages: https://leonardo251207.github.io/mi-blog-dev/
> Repositorio: https://github.com/Leonardo251207/mi-blog-dev
>
> Autor: Leonardo Nucamendi Ruiz — Ingeniería en Tecnologías de la Información e Innovación Digital.

**Visibilidad:** "No listado" si solo necesitas compartir el enlace; "Público" si el profe pide que sea público.

---

## 10. Guion de respaldo si algo falla en vivo

| Problema | Qué decir / hacer |
|---|---|
| Render no despierta | "El plan gratuito de Render duerme los servicios; mientras despierta, les muestro la versión local, que es exactamente la misma aplicación." |
| La API local no responde | Revisa la ventana de PowerShell; si se cerró, ejecuta `.\start-all.ps1` y espera 5 segundos. |
| El blog muestra tarjetas de respaldo | "Como ven, el blog degrada correctamente: si la API falla, muestra contenido estático en lugar de romperse." |
| GraphQL devuelve cero | Visita el blog otra vez, espera 5 segundos y recarga la consulta. "El beacon tarda unos segundos en registrar la visita." |
| La consola da 401 | Verifica que sea `console-dev-token` en local; en producción es el token generado por Render. |
| La landing no cambia | "Primero guardé el borrador y después publiqué; el sitio público solo lee la versión publicada." |
| Métricas del panel en cero o no disponibles | "El servicio de métricas está despertando o no responde; el CMS me lo indica sin romper la consola." |
| La publicidad no aparece | Revisa que el interruptor **activa** esté encendido y recarga la portada. |
| Se ve lento | "Estamos en la capa gratuita; el primer acceso siempre es el más lento." |

---

## 11. Resumen de una página (para estudiar antes de grabar)

**Qué es:** un CMS API-First con blog estático, landing editable, publicidad configurable, métricas GraphQL y generador de HTML.

**Cómo funciona:** el blog pide artículos y la landing al CMS; el CMS guarda en SQLite (local) o MongoDB (producción); el beacon manda visitas a métricas; la consola administra blog, landing, publicidad y el resumen de métricas.

**Qué decisioné:** contrato primero, tokens con scopes, idempotencia, rate limit, cursor firmado, ETag, repositorio intercambiable, landing con borrador/publicada, publicidad activa/inactiva, pruebas y documentación.

**Qué probé:** 74 pruebas (57 + 13 + 4) y verificación manual en el navegador.

**Dónde está:** Render (3 servicios), Vercel y GitHub Pages; Render gratis se duerme 30–60 s.

**Cómo usé IA:** como copiloto para ordenar, generar, probar y depurar; yo decidí, revisé y verifiqué.

**Frase de cierre:** "Si no lo puedo explicar, no lo puedo defender."
