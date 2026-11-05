# Captura multi-sitio: observar lo que no necesariamente administras

> El sistema no es "la analítica de mi blog". Es un **observador de sitios**. Un sitio puede
> ser tuyo (GitHub Pages, Vercel) o ajeno (un blog público), y de cada uno solo puedes medir
> lo que su canal de captura permite.

---

## 1. El cambio de mentalidad

Antes: "tengo un blog y quiero sus métricas".
Ahora: "tengo una lista de sitios que quiero observar, y cada uno me da acceso a cosas distintas".

Eso obliga a separar tres conceptos que antes eran uno:

- **El sitio** — el sujeto observado. No implica propiedad ni administración.
- **El dominio** — un host concreto por el que se sirve el sitio. Es un alias, no la identidad.
- **El canal de captura** — la vía por la que llegan sus datos. Determina qué es medible.

Un sitio sin canal es solo un nombre. Un canal sin sitio no existe. Y **la cobertura no es
uniforme**: un sitio con beacon mide personas; un sitio con edge mide personas y bots; un
sitio ajeno solo se puede sondear desde fuera.

### 1.1 El dominio es un alias, no una identidad

El identificador estable es el `slug`. El dominio cambia:

- `usuario.github.io` cambia si cambias de usuario o de repo.
- `proyecto.vercel.app` cambia en cada preview.
- Un dominio propio caduca o migra.

Por eso el modelo guarda los dominios como entidades con estado (`PENDIENTE`, `VERIFICADO`,
`RETIRADO`) y vigencia. Retirar un dominio no borra el histórico: los eventos conservan el
`host` que los produjo. Una propiedad está verificada cuando al menos un dominio lo está; los
hosts efímeros pueden quedarse en `PENDIENTE` con cuota baja.

```
Sitio ──┬── Canal BEACON        → pageviews, sesiones, engagement
        ├── Canal EDGE          → peticiones, bots, estados, bytes
        ├── Canal API EXTERNA   → GA4, Search Console, anuncios
        ├── Canal SINTÉTICO     → disponibilidad y latencia desde fuera
        └── Canal IMPORTACIÓN   → histórico cargado a mano
```

---

## 2. La matriz de capacidades

Esto es lo que decide qué puedes prometer en el panel. Si un sitio no tiene canal para una
métrica, el panel no debe mostrarla vacía: debe decir **"no observable con los canales
actuales"**.

| Plataforma | Beacon (JS) | Edge / logs | API externa | Sonda sintética |
|------------|-------------|-------------|-------------|-----------------|
| **GitHub Pages** | Sí, añadiendo un script al HTML | **No** (no hay servidor) | GA4 / Search Console si los conectas | Sí |
| **Vercel** | Sí | Sí (middleware, funciones, log drains) | GA4 / Search Console / AdSense | Sí |
| **WordPress** | Sí (script o plugin) | Sí (servidor o plugin) | GA4 / AdSense / Search Console | Sí |
| **Sitio ajeno** | No | No | Solo si te dan acceso | Sí |
| **API propia** | No aplica | Sí (instrumentación) | — | Sí |
| **Cloudflare delante** | Sí | Sí (logs del edge) | — | Sí |

Lectura rápida:

- **GitHub Pages** te da personas, no bots. No hay logs de servidor porque no hay servidor.
- **Vercel** te da las dos cosas si añades middleware o log drain.
- **Un sitio ajeno** no te da tráfico real. Solo puedes comprobar que responde.
- **Poner Cloudflare delante** de un sitio estático es la forma más barata de obtener logs
  de bots sin cambiar de hosting.

---

## 3. Qué habilita cada canal

| Canal | Métricas que aporta | Lo que **no** puede dar |
|-------|---------------------|--------------------------|
| **Beacon** | pageviews, sesiones, visitantes, engagement, scroll, web vitals, referrer, dispositivo | Bots (no ejecutan JS), errores de servidor, bytes |
| **Edge** | todas las peticiones, UA, bots, estados, bytes, latencia, rutas | Engagement (no hay JS), sesiones humanas fiables |
| **API externa** | agregados de GA4, Search Console, anuncios | Eventos crudos, tiempo real, bots |
| **Sintético** | disponibilidad, latencia, TLS, redirecciones, tamaño de respuesta | Tráfico real, bots, personas |
| **Importación** | histórico puntual | Frescura, continuidad |

**Consecuencia de diseño:** el catálogo de métricas deja de ser global. Cada definición
declara qué canales la habilitan, y el catálogo de un sitio se filtra por sus canales
activos.

```
DefiniciónDeMétrica {
  clave, unidad, agregación,
  canalesRequeridos: [BEACON, EDGE, API_EXTERNA, ...],
  dimensionesPermitidas
}
```

---

## 4. Plataforma por plataforma

### GitHub Pages

- Es estático: no hay servidor, no hay logs, no hay middleware.
- Puedes añadir un `<script>` al HTML y obtener beacon.
- No puedes definir cabeceras propias, así que el colector debe aceptar CORS desde el dominio
  del sitio (`*.github.io` o dominio propio).
- Los bots **no** aparecen: no ejecutan JavaScript.
- Si necesitas bots, pon Cloudflare delante o muévete a un hosting con edge.

### Vercel

- Beacon para personas.
- Middleware o funciones para emitir visitas al colector en cada petición.
- Log drains para el flujo completo, incluidos bots y estáticos.
- Cuidado: el middleware se ejecuta en cada petición; si emites de forma síncrona, pagas
  latencia y cómputo. Mejor encolar o muestrear.
- Puedes empezar con beacon y añadir edge después, sin cambiar el modelo.

### WordPress

- Beacon por script o plugin.
- Logs del servidor para bots.
- GA4, AdSense y Search Console como APIs externas.
- Es el caso más completo, pero también el más pesado de operar.

### Sitio ajeno

- No puedes inyectar JS ni leer logs.
- Solo sonda sintética: disponibilidad, latencia, TLS.
- Si el dueño te da acceso a su GA4 o Search Console, añades API externa.
- **No intentes inferir su tráfico rastreándolo**: estarías midiendo tu rastreador, no sus
  visitantes.

### API propia

- No hay beacon: instrumentas el servidor.
- Útil para medir agentes que consumen tu API, no una web.

---

## 5. Arrancar sin tener una web

No necesitas un blog en producción para validar el sistema. Necesitas **canales**, no
contenido.

1. **Sitio de laboratorio.** Un sitio declarado como `LABORATORIO` con una página estática
   mínima. Sirve para probar beacon, ingesta y panel.
2. **Sonda sintética sobre sitios públicos.** Apunta el canal sintético a sitios reales que
   te interesen. Desde el primer día tienes disponibilidad y latencia sin ser el dueño.
3. **Datos sembrados.** Un generador de eventos con formas realistas permite probar reportes
   y agregaciones antes de tener tráfico.
4. **Un despliegue pequeño en Vercel.** Cuando quieras edge de verdad, un proyecto gratuito
   con middleware basta para ver bots.
5. **Cloudflare delante de GitHub Pages.** Si quieres logs de bots sobre un sitio estático.

El orden recomendado: sintético (hoy) → beacon en laboratorio (esta semana) → edge en Vercel
(cuando haya algo desplegado) → APIs externas (cuando tengas GA4 o Search Console).

---

## 6. Límites honestos

- **Sin JavaScript no hay beacon.** Un bot no ejecuta JS, así que el beacon nunca lo verá.
- **Sin logs no hay bots.** Un sitio estático sin proxy no puede saber quién lo rastrea.
- **Sin acceso delegado no hay API externa.** No puedes leer el GA4 de otro sin permiso.
- **Una sonda no es tráfico.** Mide tu sonda, no a los visitantes.
- **Observar no es bloquear.** El sistema registra; no impide la petición. Bloquear exige un
  ejecutor en el edge y una política activa, que hoy están fuera de alcance.
- **La cobertura es desigual.** Dos sitios en el mismo panel pueden tener métricas distintas,
  y eso debe ser visible, no silencioso.

Esto no es una debilidad del modelo: es la realidad de la observación. El sistema la hace
explícita en lugar de inventar números.

---

## 7. Qué NO es este sistema

No es un CRM, ni un CMS, ni un panel editorial. Por eso el modelo **no** tiene:

- Artículos, autores, categorías ni flujos de publicación.
- Usuarios finales, leads ni segmentos de clientes.
- Gestión de contenido o de campañas.

Solo tiene **sitios, canales y mediciones**. La superficie de administración existe únicamente
para declarar qué se observa y con qué credenciales. Configurar una fuente no es administrar
un negocio.

Si algún día necesitas atribuir métricas a contenido, se añade un **catálogo de contenido de
solo lectura**, no un CMS.

---

## 8. Impacto en el modelo

| Concepto | Cambio |
|----------|--------|
| `Propiedad` | Pasa a significar **sitio observado**, no sitio administrado |
| `DominioDePropiedad` | Entidad nueva: host con estado y vigencia; el `slug` sigue siendo la identidad |
| `CanalDeCaptura` | Entidad nueva: vía de ingreso, estado, modo de origen y cobertura |
| `DefiniciónDeMétrica` | Declara qué canales la habilitan y si está activa |
| `Procedencia` | Añade el canal de origen, no solo la fuente |
| `ReglaDeAlerta` | Entidad nueva: qué vigilar, cuándo avisar y por dónde |
| Panel | Muestra cobertura por sitio y explica qué falta para medir X |
| Roadmap | El canal sintético permite empezar antes de tener web propia |
