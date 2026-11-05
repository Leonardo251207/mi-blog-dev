# Guía práctica: observar tráfico de agentes de IA y bots

> Para alguien que empieza en analítica, SEO, SRE y producto. El objetivo **no** es cobrar:
> es entender qué nos visita, cuánto consume y qué decisiones tomar con eso.

---

## 1. Primero, ordenar el vocabulario

No todo lo que no es humano es lo mismo. La categoría cambia la decisión.

| Categoría | Qué hace | Ejemplos de UA (verificar vigencia) | ¿Nos conviene? |
|-----------|----------|-------------------------------------|----------------|
| **Buscador clásico** | Indexa para resultados de búsqueda | `Googlebot`, `Bingbot`, `YandexBot` | Sí: trae visitas humanas |
| **Entrenamiento de IA** | Recopila contenido para modelos | `GPTBot`, `ClaudeBot`, `CCBot`, `Bytespider`, `meta-externalagent` | Neutro: no trae tráfico, consume ancho de banda |
| **Búsqueda con IA** | Indexa para responder citando fuentes | `OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot` | Sí, si te citan: puede traer referidos |
| **Fetcher por usuario** | Un humano pidió a la IA abrir tu página | `ChatGPT-User`, `Perplexity-User` | Sí: es demanda real, aunque automatizada |
| **Scraper / SEO tool** | Extrae datos para terceros | `AhrefsBot`, `SemrushBot`, `MJ12bot` | Depende: consume sin aportar |
| **Monitorización** | Comprueba que el sitio responde | `UptimeRobot`, `PingdomBot` | Sí: es tu propia operación |
| **Previsualización social** | Genera tarjetas al compartir | `facebookexternalhit`, `Twitterbot`, `LinkedInBot` | Sí: afecta a cómo se ve el enlace |

Dos matices que cuestan tiempo a los principiantes:

- **`Google-Extended` no es un user-agent.** Es un token de `robots.txt` que controla el uso
  del contenido para Gemini/entrenamiento, aunque quien rastrea sea Googlebot. No lo verás en
  los logs.
- **Un UA se puede falsificar.** Cualquiera puede escribir `Googlebot`. Por eso la
  verificación (IP, DNS inverso, firma) es lo que separa "declara ser" de "es".

---

## 2. Las dos lentes que hay que mirar siempre

> **Requisito de observación.** La lente A necesita acceso a las peticiones (edge, logs o
> proxy). En un sitio estático sin servidor —GitHub Pages sin CDN delante, por ejemplo— no hay
> bots observables. La lente B necesita beacon o GA4. Sin canal, no hay dato: el panel debe
> decirlo, no inventarlo.

### Lente A — Actividad del rastreador (lo que ves en tu servidor)

Es 100 % medible: peticiones, rutas, bytes, códigos de estado, tiempos, IP, ASN.
Responde: *¿quién viene, cuánto y a por qué?*

### Lente B — Referidos de IA (lo que ves en tu analítica web)

Es medible solo cuando un humano hace clic desde una respuesta de IA. Se detecta por
`referrer`: `chatgpt.com`, `perplexity.ai`, `copilot.microsoft.com`, `gemini.google.com`,
`claude.ai`… Responde: *¿la IA nos está enviando personas?*

**No las mezcles.** Un bot que te rastrea 10.000 veces no es "tráfico". Un referido de IA es
un humano. Son dos gráficas distintas y cuentan historias distintas.

Lo que **no** puedes saber desde el servidor: si tu contenido se usó para entrenar, qué
respondió el modelo, o cuántas veces te citó sin clic. Cualquier panel que prometa eso está
inventando.

---

## 3. El marco de decisión

Para cada agente o categoría, responde cinco preguntas:

1. **¿Quién es?** Identidad declarada y verificada.
2. **¿Para qué viene?** Propósito (indexar, entrenar, responder a un usuario, extraer).
3. **¿Cuánto consume?** Peticiones, bytes, rutas, frecuencia.
4. **¿Qué me cuesta?** Egress, CPU, base de datos, caché.
5. **¿Qué me aporta?** Indexación, referidos, visibilidad, o nada.

Con eso, las decisiones posibles son:

| Decisión | Cuándo | Cómo se implementa |
|----------|--------|--------------------|
| **Permitir** | Aporta o es inocuo | Nada |
| **Permitir con caché** | Consume mucho y pide lo mismo | CDN/caché por ruta |
| **Limitar** | Consumo desproporcionado | Rate limit por agente |
| **Bloquear** | Coste sin retorno o contenido sensible | `robots.txt` + regla de edge |
| **Negociar / licenciar** | Uso comercial de contenido | Acuerdo, no código |

Cobrar queda **fuera de alcance**: sin acuerdo, sin contraparte y sin volumen, no se modela.

Empieza por **medir y permitir**. Bloquear sin datos es una decisión emocional.

---

## 4. Qué medir (y por qué)

| Métrica | Definición | Para qué sirve |
|---------|------------|----------------|
| Peticiones por clase | Volumen por categoría de agente | Saber cuánto del tráfico no es humano |
| Cuota de tráfico | % de peticiones por agente | Detectar quién domina |
| Bytes servidos | Egress atribuido | Estimar coste real |
| Rutas más rastreadas | Top de patrones de ruta | Ver qué contenido les interesa |
| Códigos servidos | 200/301/404/410/429 | Detectar desperdicio de rastreo |
| Tasa de 404 | % de peticiones a rutas inexistentes | Arreglar enlaces o redirigir |
| Ratio bot/humano | Peticiones de agentes vs pageviews | Contexto de magnitud |
| Nuevos agentes por semana | UA no vistos antes | Descubrir actores emergentes |
| Fallos de verificación | UA dice X pero no verifica | Detectar suplantación |
| Tiempo de respuesta por clase | Latencia p50/p95 | Ver si los bots degradan el servicio |
| Referidos de IA | Sesiones con referrer de IA | Medir el retorno real |
| Coste por 1.000 peticiones | Egress + cómputo / volumen | Poner precio al problema |

**Regla de producto:** cada métrica debe tener una acción asociada. Si no cambiaría ninguna
decisión, no la construyas.

---

## 5. Cómo clasificar sin sobreingeniería

Hazlo en tres niveles y para cuando el nivel actual responda tus preguntas.

### Nivel 1 — Lista de patrones (una tarde)

- Un catálogo versionado de agentes con su patrón de UA y su categoría.
- Emparejamiento por expresión regular, sin distinguir mayúsculas.
- Resultado: 70–80 % del tráfico identificado con muy poco esfuerzo.
- Riesgo: suplantación y UA nuevos.

### Nivel 2 — Verificación de identidad (una semana)

- **DNS inverso confirmado** para los grandes (Googlebot, Bingbot): se resuelve la IP a un
  dominio del operador y se vuelve a resolver el dominio a la misma IP.
- **Rangos de IP publicados** por el operador (Google publica JSON con sus rangos).
- **Firma criptográfica de mensajes** (`Signature-Agent` / HTTP Message Signatures) cuando el
  operador la ofrece. Es el estándar emergente y el más fiable.
- Resultado: distingues agente real de impostor.

### Nivel 3 — Comportamiento (cuando haga falta)

- No ejecuta JavaScript pero pide HTML agresivamente.
- No descarga CSS, imágenes ni fuentes.
- Patrón de rutas típico de extracción (sitemap, artículos en serie).
- Velocidad y concurrencia anómalas.
- ASN inesperado para ese agente.
- Resultado: una puntuación de sospecha, no una certeza.

Cada visita guarda las **evidencias** que la clasificaron. Así puedes explicar por qué
decidiste algo y revisar el criterio más adelante.

---

## 6. Qué construir, en orden

### Semana 1–2: la base

- Registro estructurado de accesos en el edge: fecha, ruta, UA, IP, estado, bytes, duración.
- Catálogo inicial de ~30 agentes conocidos.
- Nada de dashboards todavía.

### Semana 3–4: la primera vista

Seis widgets, ni uno más:

1. Peticiones por clase (humano / buscador / IA / scraper / monitor).
2. Top 10 agentes por volumen.
3. Bytes servidos por clase.
4. Top rutas rastreadas.
5. Códigos de respuesta servidos a agentes.
6. Serie temporal de peticiones por categoría.

### Semana 5–6: verificación

- DNS inverso y rangos de IP para los agentes grandes.
- Panel de "declarado vs verificado".
- Alerta cuando un agente conocido empieza a fallar verificación.

### Semana 7–8: decisiones

- Comparar coste estimado por agente con referidos atribuidos.
- Proponer cambios de `robots.txt` o de caché con datos delante.
- Medir el efecto del cambio: antes/después, misma ventana y misma estacionalidad.

### Después (opcional)

- Políticas por ruta, desafíos y, solo mucho después, bloqueo. Monetización, fuera de alcance.

---

## 7. Lo mínimo de SEO que necesitas

Tres piezas, no más:

### Search Console (lo que Google ve de ti)

- **Impresiones**: cuántas veces apareciste.
- **Clics**: cuántas veces te eligieron.
- **CTR**: clics / impresiones.
- **Posición media**: dónde apareces.
- **Consultas y páginas**: el cruce que importa.
- **Indexación**: qué está indexado y qué no.

Qué revisar cada semana:

- Páginas que pierden impresiones (¿contenido viejo? ¿competencia?).
- Páginas con muchas impresiones y CTR bajo (título o descripción débiles).
- Consultas nuevas (oportunidades de contenido).
- Páginas indexadas que no deberían estarlo (parámetros, duplicados).

### GA4 (lo que pasa cuando llegan)

- Sesiones, usuarios, engagement, duración.
- Canales de adquisición.
- Páginas de aterrizaje.
- Eventos clave (si defines alguno).

Cuidado: GA4 muestrea y agrega. No cuadra al pageview con tu propio contador, y está bien.
Por eso el modelo guarda la procedencia y no suma fuentes.

### El puente entre ambos

- Une por **página**: Search Console da consultas por URL; GA4 da comportamiento por URL.
- Las URLs con parámetros rompen la unión: normaliza a patrón de ruta.
- Los referidos de IA van en su propio canal, no dentro de "referral" genérico.

**Un dato clave para tu caso:** el tráfico deI un rastreador de IA no aparece en GA4 (no
ejecuta JavaScript). Si solo miras GA4, eres invisible a los agentes. Por eso este proyecto
tiene captura propia en el servidor.

---

## 8. Lo mínimo de SRE que necesitas

No necesitas on-call 24/7 para una API privada. Necesitas saber **cuándo el dato deja de ser
fiable**.

### SLIs (lo que mides)

| Servicio | SLI | Objetivo razonable |
|----------|-----|--------------------|
| Ingesta | % de lotes aceptados | 99,5 % |
| Ingesta | latencia p95 de aceptación | < 200 ms |
| Agregación | retraso del último cubo | < 15 min |
| Consulta | latencia p95 de reporte de 30 días | < 800 ms |
| Sincronización | % de ejecuciones correctas | > 98 % |
| Frescura | antigüedad del dato de cada integración | < 24 h |

### Los tres avisos que sí importan

1. **El dato está viejo.** La integración X no actualiza hace más de N horas.
2. **La ingesta falla.** Tasa de error por encima del umbral durante 10 minutos.
3. **El coste se dispara.** Peticiones o bytes de una clase crecen de forma anómala.

Todo lo demás (CPU, memoria) es secundario para este producto. Un panel de métricas que
miente es peor que no tener panel.

### Hábitos

- Un panel por servicio, con cuatro gráficas: volumen, errores, latencia, frescura.
- Un runbook de una página por alerta: qué significa, qué mirar, qué hacer.
- Revisión semanal de 15 minutos: ¿qué cambió?
- Error budget: si el objetivo se rompe, se para producto y se arregla la fiabilidad.

---

## 9. Lo mínimo de product engineering

La trampa clásica es construir dashboards que nadie usa. El ciclo útil es:

```
pregunta → métrica → decisión → acción → medición del efecto
```

Ejemplo real de este proyecto:

1. **Pregunta:** ¿los rastreadores de IA nos cuestan más de lo que nos aportan?
2. **Métrica:** bytes servidos por categoría vs sesiones referidas por IA.
3. **Decisión:** limitar la categoría X en las rutas más costosas.
4. **Acción:** regla de caché o `robots.txt`.
5. **Efecto:** comparar 30 días antes/después con la misma estacionalidad.

Principios:

- **Una métrica sin acción es decoración.**
- **Prefiere ratios y tendencias a totales.** "10.000 peticiones" no dice nada; "el 38 % del
  tráfico es de agentes y creció 12 % en un mes" sí.
- **Mide el efecto de tus decisiones.** Sin antes/después no aprendes, solo opinas.
- **Escribe la decisión.** Un registro de "qué decidimos y por qué" vale más que el panel.

---

## 10. Errores comunes de quien empieza

1. **Creer que todo bot es malo.** Muchos son tu distribución.
2. **Bloquear por reflejo.** Pierdes indexación y visibilidad sin saber qué ganaste.
3. **Mirar solo GA4.** Los agentes no ejecutan JS: son invisibles ahí.
4. **Sumar fuentes distintas.** Tu contador, GA4 y Search Console nunca coinciden.
5. **Confiar en el UA.** Es una declaración, no una prueba.
6. **Construir 20 widgets.** Nadie los mira. Seis bien elegidos bastan.
7. **Alertar de todo.** El ruido enseña a ignorar las alertas.
8. **Optimizar antes de medir.** Primero el dato, luego el índice, luego la caché.

---

## 11. Glosario mínimo

- **Agente**: programa autónomo que accede al sitio sin humano delante.
- **Rastreador (crawler)**: recorre enlaces para descubrir e indexar.
- **Fetcher**: obtiene una URL concreta, normalmente a petición de un usuario.
- **Scraper**: extrae datos para un fin propio, sin contrato de indexación.
- **UA (user-agent)**: cadena que el cliente declara ser. Falsificable.
- **ASN**: red/organización de la que proviene una IP.
- **DNS inverso confirmado**: la IP resuelve a un dominio que vuelve a resolver a la IP.
- **Pageview**: carga de página. Distinto de sesión y de visitante.
- **Sesión**: conjunto de interacciones con la misma clave rotativa.
- **Cubo (bucket)**: intervalo temporal agregado (hora, día).
- **Procedencia**: de dónde viene un dato y cuán fresco es.
- **SLI / SLO**: lo que mides / el objetivo que te comprometes a cumplir.
- **Error budget**: margen de fallo que te permite el objetivo.
