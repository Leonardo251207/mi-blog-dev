# Segmentación del código en una arquitectura N-tier

> Guía de estructura. F1 ya implementa las capas de propiedades, navegación, consulta e
> ingesta; los módulos de conectores, workers y alertas quedan como siguientes cortes.

## 1. La idea central

N-tier puro (presentación → negocio → datos) funciona hasta que el negocio crece y la capa
central se convierte en un bloque de miles de líneas. La solución no es abandonar N-tier:
es **usar N-tier como eje horizontal y módulos por dominio como eje vertical**.

```
        ┌──────────────────────────────────────────────────┐
        │  Presentación   (consulta: tipos y operaciones)  │
        ├──────────────────────────────────────────────────┤
        │  Aplicación     (casos de uso, autorización)     │
        ├──────────────────────────────────────────────────┤
        │  Dominio        (entidades, reglas, políticas)   │
        ├──────────────────────────────────────────────────┤
        │  Persistencia   (repositorios, agregaciones)     │
        │  Integración    (GA4, AdSense, Search Console)   │
        └──────────────────────────────────────────────────┘
             propiedades │ navegación │ analítica │ agentes │ alertas │ operación
```

Cada módulo vertical tiene su rebanada de cada capa. Las capas siguen existiendo y las
reglas de dependencia se respetan **dentro** de cada módulo.

Por qué encaja una **superficie de consulta tipada**: en REST la "presentación" son endpoints
y suele diluirse. Una superficie de consulta es un **contrato tipado** (tipos, entradas,
operaciones) que se puede aislar limpiamente del negocio. Ese contrato no es el modelo de
dominio ni el modelo de Mongo: es la vista que se promete al consumidor.

> **Convención de nombres.** Las puertas se nombran por **rol**, no por tecnología:
> `query` (consulta y administración), `ingest` (telemetría por lotes), `ops` (sondas),
> `export` (descargas) y `stream` (empuje). La tecnología vive en el adaptador
> (`entrypoints/query/graphql/`) y en la decisión tecnológica, nunca en el nombre de la
> puerta.

---

## 2. Capas: qué va y qué no

| Capa | Responsabilidad | Sí va aquí | No va aquí |
|------|-----------------|-----------|------------|
| **Presentación / consulta** | Traducir operaciones de consulta a casos de uso | Tipos, entradas, enums, resolvers finos, contexto de petición, formateo de errores, límites de profundidad y coste, cargadores por lote | Reglas de negocio, consultas a Mongo, cálculo de métricas |
| **Aplicación** | Orquestar un caso de uso completo | Servicios de caso de uso, DTOs de salida, transacciones, comprobación de permisos por propiedad, validación de entrada semántica, composición de reportes | Detalles del adaptador de consulta, drivers de base de datos, llamadas HTTP a terceros |
| **Dominio** | Modelar el negocio y sus invariantes | Entidades, objetos de valor, políticas (clasificación de agentes, elegibilidad, precios), eventos de dominio, puertos (interfaces) | FastAPI, Strawberry, PyMongo, Pydantic como modelo de dominio, I/O |
| **Persistencia** | Guardar y recuperar | Repositorios que implementan puertos, documentos Mongo, índices, pipelines de agregación, caché | Reglas de negocio, forma del contrato de consulta |
| **Integración** | Hablar con el mundo exterior | Clientes GA4/AdSense/Search Console, mapeo de respuestas externas a DTOs propios, reintentos, cuotas, secretos | Lógica de reporte, decisiones de producto |
| **Trabajadores** | Procesos fuera de la petición | Agregación por cubos, sincronización programada, reclasificación de visitas | Código duplicado del dominio (reutiliza la capa de aplicación) |

**Regla de oro:** la dirección de dependencia siempre apunta hacia dentro.

```
presentación ──► aplicación ──► dominio
persistencia ──► dominio
integración  ──► aplicación (puertos)
```

El dominio no importa nada de las capas externas. Si mañana cambias el adaptador de consulta
o Mongo por Postgres, la capa de aplicación y el dominio no se tocan.

---

## 3. Estructura de carpetas propuesta

Adaptada al proyecto. `billing` no aparece: la monetización está fuera de alcance. `alerts`
sí aparece porque las alertas forman parte del alcance (panel + Telegram/Discord).

```
app/
  main.py                     # monta las puertas de entrada
  bootstrap/
    settings.py               # configuración tipada por entorno
    container.py              # composición: qué implementación se inyecta
    lifespan.py               # arranque/parada de clientes y workers
  shared/                     # transversal, sin dependencias de módulos
    errors.py                 # jerarquía de errores de negocio
    auth.py                   # principal, scopes, guardas de propiedad
    time.py                   # rangos, zonas horarias, cubos
    pagination.py             # cursores
    telemetry.py              # trazas, métricas, logs
    ids.py                    # identificadores deterministas
    outbox.py                 # entrega fiable de notificaciones
  entrypoints/                # una carpeta por puerta, nombrada por rol
    query/                    # superficie de consulta
      graphql/                # adaptador concreto de hoy
        schema.py             # ensambla el contrato de todos los módulos
        context.py            # principal, cargadores, trazabilidad
        scalars.py            # DateTime, Date, Long, JSON, Money
        errors.py             # error de negocio → error de contrato
        directives.py         # auth, coste, deprecación
    ingest/
      routes.py               # POST /v1/collect
      validators.py           # validación de lote y deduplicación
    ops/
      routes.py               # /health, /ready, /metrics
    export/
      routes.py               # /v1/exports
    stream/
      routes.py               # /v1/stream (opcional)
  modules/
    properties/               # tenencia, dominios y acceso
      api/                    # tipos, consultas y comandos que expone
      application/            # casos de uso y DTOs
      domain/                 # entidades y reglas
      persistence/            # repositorios y documentos
    navigation/               # eventos propios, sesiones, agregados
    analytics/                # GA4 normalizado y reportes
    ads/                      # publicidad normalizada
    agents/                   # registro, identidad, clasificación, visitas
    alerts/                   # reglas, deduplicación, outbox
      api/                    # tipos y comandos de alertas
      application/            # evaluación y despacho
      domain/                 # condiciones, severidad, silencio
      persistence/            # reglas, notificaciones, canales
    operations/               # salud, cuotas, auditoría, sincronizaciones
  connectors/
    ga4/                      # cliente + mapeo de la Data API
    adsense/                  # cliente + mapeo de Management API
    search_console/           # opcional, SEO
    telegram/                 # bot + envío
    discord/                  # webhook + envío
  workers/
    rollup.py                 # eventos → cubos
    sync.py                   # programador de integraciones
    classify.py               # reclasificación y verificación de agentes
    alerts.py                 # evalúa reglas y encola notificaciones
    dispatch.py               # entrega notificaciones con reintentos
tests/
  unit/                       # dominio puro
  integration/                # repositorios contra Mongo real
  contract/                   # respuestas grabadas de APIs externas
  e2e/                        # operaciones de consulta de punta a punta
```

### Por qué esta forma

- **`entrypoints/` por puerta.** El nombre de la carpeta dice el rol (`query`, `ingest`,
  `ops`, `export`, `stream`), no la tecnología. Si mañana cambia el adaptador, la puerta
  sigue llamándose igual.
- **`entrypoints/query/graphql/`.** Ahí y solo ahí aparece la tecnología concreta. Es
  reemplazable sin tocar módulos ni aplicación.
- **`modules/` por contexto, no `services/` genérico.** Un `services/` único termina siendo
  el cajón de todo. Aquí cada módulo se puede leer de arriba abajo.
- **`api/` dentro de cada módulo.** El tipo `Agent` y su operación viven junto al dominio de
  agentes, no en una carpeta global que crece sin control. Solo el ensamblado es global.
- **`connectors/` fuera de `modules/`.** Las APIs externas no son "nuestro dominio": son
  adaptadores. Su trabajo es traducir, no decidir. Telegram y Discord son conectores de
  salida, no canales de captura.
- **`alerts/` es un módulo, no una puerta.** Se evalúa desde un worker y se consulta desde la
  superficie de consulta; la entrega vive en `connectors/` y el outbox garantiza reintentos.
- **`ingest/` es una puerta, no un módulo.** Reutiliza los casos de uso de `navigation` y
  `agents`; no duplica reglas.
- **`shared/` mínimo.** Si `shared` crece, es señal de que algo debería ser un módulo.

---

## 4. Cómo se traduce una operación de consulta

Ejemplo con `traficoDeAgentes`:

1. **Presentación** recibe la operación, valida tipos y construye el `Contexto`
   (principal, propiedades permitidas, loaders, traza).
2. **Aplicación** ejecuta `ObtenerTraficoDeAgentes`: comprueba permiso sobre la propiedad,
   normaliza el rango temporal, elige desgloses y llama al repositorio.
3. **Dominio** aporta las reglas: qué es una visita verificada, cómo se calcula la cuota de
   tráfico, qué clases se agregan.
4. **Persistencia** ejecuta la agregación por cubos y devuelve filas planas.
5. **Aplicación** compone el DTO con totales, series y procedencia.
6. **Presentación** mapea DTO → tipos del contrato. Nada más.

Consecuencia práctica: **un resolutor no debería tener más de 10–15 líneas**. Si tiene más,
la lógica pertenece a la capa de aplicación.

### Dónde vive cada cosa concreta

| Necesidad | Capa | Módulo |
|-----------|------|--------|
| Comprobar que el token puede leer la propiedad X | Aplicación (`shared/auth`) | — |
| Decidir si un dominio pasa a `VERIFICADO` | Dominio | properties |
| Decidir si una visita es `agenteVerificado` | Dominio (política de clasificación) | agents |
| Guardar la visita | Persistencia | agents |
| Consultar los últimos 30 días por agente | Persistencia (agregación) | agents |
| Calcular la cuota de tráfico por agente | Aplicación + dominio | agents |
| Evaluar si una regla de alerta dispara | Dominio (condiciones y silencio) | alerts |
| Entregar un mensaje a Telegram o Discord | Integración (`connectors/`) | — |
| Traducir la respuesta de GA4 a mediciones | Integración (`connectors/ga4`) | — |
| Decidir qué métricas expone el reporte GA4 | Aplicación | analytics |
| Paginar por cursor | Presentación + persistencia | transversal |
| Llenar `agente` en 50 visitas sin 50 consultas | Presentación (DataLoader) | agents |

---

## 5. El problema del N+1 en la resolución campo a campo

Una superficie que resuelve campo por campo —el caso de GraphQL— invita a este error: si
`visitasDeAgentes` devuelve 50 visitas y cada una resuelve su `agente` con una consulta, son
51 viajes a Mongo.

Solución por capas:

- **Presentación:** un cargador por petición (un `DataLoader` en el adaptador actual), que
  agrupa claves y resuelve en lote.
- **Persistencia:** un método `buscarPorIds(ids)` que hace una sola consulta.
- **Aplicación:** no participa; no debe saber cómo se resuelve el contrato.

Regla: **todo campo que cruce una frontera de agregado se resuelve con cargador**. Si no,
el tiempo de respuesta crece de forma lineal con el tamaño de la página.

---

## 6. Módulos que se comunican entre sí

Hay dos formas y conviene elegir conscientemente:

1. **Llamada a caso de uso** (síncrona, explícita). El módulo `agents` necesita saber si una
   propiedad recolecta agentes: pide el dato a `properties` por su interfaz de aplicación.
   Ventaja: una sola verdad. Coste: acoplamiento.
2. **Modelo de lectura compartido** (CQRS ligero). El panel consulta una vista materializada
   que ya mezcla tráfico, analítica y agentes. Ventaja: rapidez. Coste: hay que mantenerla.

Recomendación: **casos de uso para escribir y decidir; vistas materializadas para leer**.
Nunca leer directamente las colecciones de otro módulo desde su persistencia.

Para el MVP, un módulo `reporting` (solo lectura) que compone las vistas del panel es más
simple que orquestar cinco llamadas. Se justifica porque la API es de consulta.

---

## 7. La excepción: la ingesta

La superficie de consulta es el contrato de **lectura y administración**. La captura de
navegación y de visitas de agentes es **alto volumen de escritura**: necesita lote,
deduplicación y respuesta rápida. Por eso:

- **`POST /v1/collect`** (lote, fuera de la superficie de consulta) recibe lotes y responde `202`.
- Comparte validación, deduplicación y casos de uso con el resto.
- Existe además una operación equivalente en la superficie de consulta para reprocesos y
  backoffice.

Esto no rompe N-tier: la ingesta es otra **puerta de entrada** que reutiliza la misma capa
de aplicación. Solo cambia el adaptador.

> **Matiz sobre la implementación actual (GraphQL).** "GraphQL es malo para volumen" se
> refiere al volumen de **escritura de telemetría**, no al de consultas. Para muchas
> consultas, formas variables y datos anidados es la elección correcta. Y no es más rápido
> que REST por naturaleza: gana en número de viajes y en ajuste de la forma, no en latencia
> bruta. Un endpoint REST con la misma consulta suele ser igual o más rápido porque parsea y
> valida menos.

Si más adelante el volumen lo exige, el colector escribe a una cola y un trabajador
persiste; ni el dominio ni la aplicación cambian.

---

### 7.1 El mapa completo de superficies

Cuatro superficies esenciales y dos opcionales. Todas comparten la misma capa de aplicación;
solo cambia el adaptador de entrada.

| Superficie | Estilo | Para qué | Perfil de tráfico | Autenticación |
|------------|--------|----------|-------------------|---------------|
| `/v1/query` | Consulta tipada (hoy GraphQL) | Consulta y administración | Interactivo, pocas peticiones, mucha variedad | Clave de API + scopes |
| `/v1/collect` | REST por lotes | Eventos de navegación y visitas de agentes | Alto volumen, máquina a máquina | Clave de escritura por propiedad o mTLS |
| `/health`, `/ready`, `/metrics` | REST / texto | Operación y sondas | Sondeos periódicos | Red interna |
| `/v1/exports/{id}` | REST en streaming | CSV/Parquet de reportes grandes | Bajo volumen, respuestas pesadas | Clave de API + scope |
| `/v1/policy-bundle` *(opcional)* | REST `GET` con ETag | Política versionada para el edge | Alto volumen, cacheable | mTLS |
| `/v1/stream` *(opcional)* | SSE | Actualización en vivo del panel | Medio, conexiones largas | Clave de API |

**Por qué cada una:**

- **La superficie de consulta** concentra todo lo que un consumidor explora o configura:
  reportes, filtros, desgloses y comandos de administración. Es donde la variedad de formas
  justifica un contrato tipado.
- **`/v1/collect`** existe porque la telemetría tiene forma fija, necesita éxito parcial por
  ítem, idempotencia y coste por evento cercano a cero.
- **Salud y métricas** no son API de producto: son contrato con la infraestructura. Nunca
  deben pasar por la superficie de consulta.
- **Exportación** va aparte porque la consulta serializa la respuesta en memoria; un CSV de
  500.000 filas se sirve en streaming.
- **Policy bundle** solo tiene sentido si el edge va a decidir en caliente. Si no bloqueas,
  el edge únicamente envía logs y esta superficie no existe.
- **SSE** antes que WebSocket o subscripciones: para un panel interno, un canal de solo
  lectura es suficiente.

**Lo que no hace falta en el MVP:** gRPC (salvo comunicación interna de altísimo volumen),
servidor OAuth2 propio, webhooks entrantes, un CRUD REST espejo de cada tipo del contrato, y
WebSockets.

### 7.2 Alertas: worker + outbox, no puerta de entrada

Las alertas no son una superficie de entrada. Son tres piezas:

1. **Evaluador** (`workers/alerts.py`): lee reglas `ACTIVA` y agregados, decide si disparan.
2. **Outbox** (`notificaciones`): guarda el aviso como `PENDIENTE` antes de intentar enviarlo.
3. **Despachador** (`workers/dispatch.py`): toma pendientes, envía por el conector y registra
   el resultado con reintentos.

Por qué así:

- El envío a Telegram/Discord puede fallar o tardar; no debe bloquear la evaluación.
- El outbox garantiza que un aviso no se pierde si el proceso cae entre "disparar" y "enviar".
- La deduplicación por `claveDeduplicacion` evita spam cuando el evaluador corre cada minuto.
- La superficie de consulta solo lee reglas y notificaciones, y expone los comandos de
  administración. No hay endpoint de "enviar alerta" desde fuera.

## 8. Tiers lógicos vs. despliegue físico

N-tier lógico no obliga a microservicios. Con un equipo pequeño:

| Proceso | Qué ejecuta | Escala por |
|---------|-------------|-----------|
| `api` | consulta + ingesta | peticiones concurrentes |
| `worker` | agregación, sincronización, clasificación | cola pendiente |
| `scheduler` | dispara trabajos periódicos | tiempo |

Los tres comparten el mismo código empaquetado con distinto punto de entrada. Es un
**monolito modular**: se despliega junto y se separa solo cuando una pieza lo justifica
(por ejemplo, la ingesta si satura la API).

---

## 9. Antipatrones a evitar desde el primer día

- **Resolutor que consulta Mongo.** Rompe la capa y duplica reglas.
- **Documento de Mongo expuesto como tipo del contrato.** Acopla la presentación a la persistencia.
- **Reglas de negocio en pipelines de agregación.** El pipeline agrega; no decide.
- **`shared/` como basurero.** Todo lo que no se sabe dónde poner acaba ahí.
- **Un módulo importando la persistencia de otro.** Se comunica por aplicación o por vista.
- **Un caso de uso por campo del contrato.** Se agrupa por intención, no por campo.
- **Optimizar antes de medir.** Primero el panel y las trazas; luego los índices.

---

## 10. Cómo saber si la segmentación funciona

Tres pruebas sencillas:

1. **Prueba del reemplazo:** ¿podrías cambiar MongoDB por otro almacén tocando solo
   `persistence/`? Si la respuesta es no, hay fugas.
2. **Prueba del contrato:** ¿podrías añadir un endpoint REST o una CLI reutilizando la capa
   de aplicación sin tocar el dominio? Si no, la lógica está en el sitio equivocado.
3. **Prueba del dominio:** ¿puedes probar la clasificación de un agente sin base de datos ni
   red? Si no, hay I/O filtrado hacia el dominio.
