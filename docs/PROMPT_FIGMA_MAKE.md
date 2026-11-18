# Análisis de Figma Make y prompt para completar el diseño

## Lo que ya existe en Figma Make

Proyecto: **Modern Minimalist Developer Portfolio** (`8ucxRVCsmP873wRdEbExay`).

| Pantalla | Contenido |
|---|---|
| **Landing** (`#top`) | Nav, hero con foto, tecnologías, proyectos, certificaciones, notas "próximamente" y contacto. |
| **Artículo C++** (`#articulo-prompts-cpp`) | Hero HUD, terminal simulador de prompts con 3 pestañas, código con tooltips y comparador antes/después. |
| **Artículo voz** (`#articulo-reconocimiento-voz`) | Demo de pronunciación, módulo de matemáticas con voz y flujo de integración en Kotlin. |
| **Artículo Vercel** (`#articulo-vercel`) | Checklist pre-despliegue, asistente de 4 pasos, consola de build y estado "en línea". |

Los tres artículos son **contenido hardcodeado**: no hay listado de blog, ni lector dinámico,
ni CMS, ni métricas, ni generador.

## Lo que falta

| Área | Pantallas que faltan |
|---|---|
| Blog público | Listado de artículos, filtros por etiqueta, buscador, paginación, estado vacío. |
| Lector | Plantilla dinámica por slug, Markdown, portada, tags, fecha, tiempo de lectura, vistas. |
| CMS | Login por token, shell con pestañas, dashboard, lista de borradores/publicados, editor. |
| Landing editable | Formulario del hero, secciones, proyectos y certificaciones; borrador/publicar. |
| Publicidad | Lista, alta/edición, layouts, tema de color, imagen, CTA, activar/desactivar, preview. |
| Métricas | Tarjetas, rango de fechas, rutas, hosts, estados de carga/error, enlace a GraphiQL. |
| Generador | Generar HTML por artículo, estado del build, URL, checksum SHA-256, historial. |
| Sistema | Estados 401/404/409/429, toasts, modales, skeletons, responsive y componentes. |

---

## Prompt para Figma Make

Copia y pega el siguiente bloque en el chat de Figma Make.

```text
Trabaja sobre el proyecto existente "Modern Minimalist Developer Portfolio".
NO rediseñes la landing ni los tres artículos interactivos actuales: conserva su
estética, su contenido y su navegación. Agrega las pantallas que faltan para
convertirlo en un producto completo: blog público, lector dinámico, consola CMS,
editor de landing, publicidad, métricas y generador estático.

Todo el texto debe estar en español (México). La interfaz debe ser navegable y
responsiva. Usa datos de ejemplo realistas y un selector de "modo demo" para
poder ver los estados cargando, vacío, error y éxito sin backend.

=========================
1. SISTEMA VISUAL
=========================
Mantén el lenguaje retro-tech / terminal que ya existe:

- Fondo OLED: #050807 (principal), #0a0f0e (paneles), #0b1110 (tarjetas).
- Texto: #eef5f1; secundario #8c9c95; terciario #58675f.
- Acento principal: verde esmeralda #3df0a8.
- Acentos secundarios: cian #3de4ff, morado #b48cff, azul #5b8cff,
  amarillo #ffd23f, rojo #ff5d5d.
- Bordes: #18221f y #24352f. Líneas de 1px, esquinas rectas o radio máximo 6px.
- Tipografía: monoespaciada para etiquetas, datos, código y botones pequeños
  (JetBrains Mono o DM Mono); sans geométrica para títulos y párrafos (Manrope).
- Títulos grandes con tracking negativo; etiquetas en MAYÚSCULAS, 10-11px,
  letter-spacing 0.14em.
- Fondo de rejilla sutil en héroes, brillo radial verde, detalles tipo consola
  con prefijos "//", "[ ]", "›", "_" y "✓".
- Botón primario: fondo verde, texto casi negro. Botón secundario: borde 1px,
  fondo transparente. Hover con brillo suave, nunca sombras grandes.
- Iconografía lineal, 16px, trazo 1.5.

=========================
2. MAPA DE NAVEGACIÓN
=========================
Implementa estas rutas (hash routing está bien):

  #top                     Landing actual (no tocar)
  #blog                    Listado público del blog
  #articulo/:slug          Lector dinámico
  #articulo-prompts-cpp    Artículo existente (no tocar)
  #articulo-reconocimiento-voz  Artículo existente (no tocar)
  #articulo-vercel         Artículo existente (no tocar)
  #admin                   Login del CMS
  #admin/blog              Lista de artículos
  #admin/blog/nuevo        Editor vacío
  #admin/blog/:id          Editor con datos
  #admin/landing           Editor de la landing
  #admin/publicidad        Lista de anuncios
  #admin/publicidad/:id    Editor de anuncio
  #admin/metricas          Dashboard de métricas
  #admin/generador         Generador estático

En la landing actual, cambia "NOTAS Y EXPERIMENTACIÓN · PRÓXIMAMENTE" por una
sección que muestre 3 tarjetas reales y un botón "VER TODAS LAS NOTAS" que lleve
a #blog. En el pie agrega "BLOG" además de GitHub, LinkedIn y Correo.
El CMS nunca debe aparecer en la navegación pública: se entra por #admin.

=========================
3. BLOG PÚBLICO (#blog)
=========================
Desktop (1440):
- Nav idéntica a la landing, con enlace activo "BLOG".
- Hero compacto: etiqueta "05 · BITÁCORA PUBLICADA", título "Notas y
  Experimentación", bajada de 2 líneas y chips: "CMS API-FIRST",
  "MONGODB ATLAS", "GRAPHQL", "GENERADOR ESTÁTICO".
- Barra de herramientas: buscador con icono, filtro por etiqueta (chips) y
  contador "3 PUBLICACIONES".
- Grid de 3 columnas con tarjetas de artículo: ilustración SVG generativa,
  etiqueta, tiempo de lectura, título, resumen y "LEER MÁS →".
- Paginación "ANTERIOR / SIGUIENTE" con cursor.
- Footer igual al de la landing.

Estados:
- Cargando: 3 tarjetas skeleton con shimmer sutil.
- Vacío: panel con "Todavía no hay publicaciones" y botón "IR A LA CONSOLA".
- Error: panel "No se pudo cargar el blog" + botón "REINTENTAR".
- Filtro sin resultados: "No hay notas con esta etiqueta".

Móvil (390): una columna, buscador a ancho completo, chips con scroll horizontal.

=========================
4. LECTOR DINÁMICO (#articulo/:slug)
=========================
- Nav mínima: logo DevBlog_, botón "← VOLVER AL BLOG".
- Hero editorial: etiqueta de estado "[ TUTORIAL / DEPLOYMENT ]", H1 grande,
  por "Leonardo Nucamendi", fecha, tiempo de lectura y contador de vistas.
- Portada 16:9 opcional con borde 1px.
- Columna de lectura de 720px máximo, Markdown con:
  h2/h3, párrafos, listas, citas, enlaces verdes, tablas y bloques de código
  con barra superior tipo terminal (tres puntos), botón "COPIAR" y scroll.
- Barra lateral sticky en desktop: tags, "COMPARTIR", "VOLVER ARRIBA".
- Al final: bloque "SOBRE ESTE ARTÍCULO", tags y dos tarjetas "SIGUIENTE /
  ANTERIOR".
- Estados: cargando (skeleton), 404 ("Este artículo no existe o fue
  despublicado"), error de red, artículo sin portada.
- Los tres artículos interactivos actuales siguen funcionando igual; el lector
  dinámico es para artículos creados en el CMS.

=========================
5. LOGIN DEL CMS (#admin)
=========================
- Pantalla centrada de 520px sobre fondo oscuro con rejilla.
- Logo DevBlog_, etiqueta "CMS · CONSOLA DE ADMINISTRACIÓN".
- Título "Conecta con tu API".
- Texto: token con scope cms:write, se guarda solo en esta pestaña.
- Campo "Token de consola" tipo password con botón mostrar/ocultar.
- Botón primario "CONECTAR" a ancho completo.
- Enlace "Ver blog" y "Ver landing" en la esquina.
- Estados: idle, validando (spinner), error 401 ("Token inválido o expirado"),
  error de red ("No se pudo conectar con el CMS"), éxito (transición al panel).
- Nota inferior: "El token se genera en Render → Environment → CMS_CONSOLE_TOKEN".

=========================
6. SHELL DEL CMS (#admin/*)
=========================
- Header fijo: logo, migas de pan ("CMS / BLOG"), estado "CONECTADO" con punto
  verde, botón "VER BLOG ↗", botón "VER LANDING ↗" y "SALIR".
- Barra lateral izquierda de 240px:
  BLOG (Artículos, Nuevo artículo), LANDING, PUBLICIDAD, MÉTRICAS, GENERADOR.
  Cada ítem con icono lineal; activo con fondo verde translúcido y borde izquierdo.
- Contenido con ancho máximo 1100px y padding 32-40px.
- En móvil: barra superior con menú hamburguesa y panel deslizante.
- Un indicador discreto "MODO DEMO" arriba a la derecha con selector:
  Datos / Vacío / Cargando / Error 401 / Error 429.

=========================
7. LISTA DE ARTÍCULOS (#admin/blog)
=========================
- Encabezado: "Artículos", contador y botón "NUEVO ARTÍCULO +".
- Pestañas: TODOS · BORRADORES · PUBLICADOS.
- Tabla en desktop:
  TÍTULO (con slug debajo), ESTADO (badge BORRADOR amarillo / PUBLICADO verde),
  TAGS, LECTURA, VISTAS, ACTUALIZADO, ACCIONES (editar, ver, eliminar).
- Fila hover con borde verde. Selección múltiple opcional.
- Paginación por cursor.
- Estados: carga (filas skeleton), vacío ("Aún no hay artículos" + CTA),
  error (panel + reintentar), borrado con modal de confirmación.
- En móvil: tabla se convierte en tarjetas apiladas.

=========================
8. EDITOR DE ARTÍCULO (#admin/blog/:id)
=========================
- Cabecera: "Editar artículo" o "Nuevo artículo", badge de estado, botones
  "GUARDAR BORRADOR", "PUBLICAR" y "VER ARTÍCULO ↗".
- Layout de dos columnas: editor 2/3, panel lateral 1/3.
- Editor:
  - Título grande sin borde.
  - Slug con prefijo "/articulo.html?slug=" y botón "REGENERAR".
  - Resumen (textarea 3 líneas, contador 180).
  - Contenido Markdown en editor monoespaciado con números de línea.
  - Pestañas "EDITAR" / "VISTA PREVIA"; la vista previa renderiza Markdown.
  - Barra de herramientas: negrita, cursiva, código, enlace, lista, cita.
  - Estado del documento: "Guardado hace 2 min" / "Cambios sin guardar".
- Panel lateral:
  - Estado: borrador/publicado con toggle.
  - Etiquetas: input con chips.
  - Tiempo de lectura calculado.
  - Fecha de publicación.
  - Portada: URL o selector.
  - "GENERAR HTML ESTÁTICO" con estado del build.
  - Zona de peligro: eliminar artículo.
- Estados: guardando, error 409 slug duplicado (bajo el campo), 422 validación,
  429 con "Reintentar en 30 s", éxito con toast.

=========================
9. LANDING EDITOR (#admin/landing)
=========================
- Cabecera: "Landing editable", meta "Borrador: fecha · Publicado: fecha",
  botones "RECARGAR", "PUBLICAR LANDING", "GUARDAR BORRADOR".
- Aviso: "El sitio público solo muestra la versión publicada".
- Formulario en secciones colapsables:
  1. HERO: etiqueta, nombre, apellido, rol, ubicación, tagline, texto y URL del
     CTA, nota y URL de foto.
  2. TECNOLOGÍAS: etiqueta y título de sección + lista editable (nombre, icono,
     color). Botón "+ AÑADIR TECNOLOGÍA".
  3. PROYECTOS: etiqueta y título + lista (badge, título, descripción, URL,
     texto del enlace, estilo de arte: verde/morado/puntos).
  4. CERTIFICACIONES: etiqueta y título + lista (emisor, título, tag, URL del
     PDF, color).
  5. NOTAS: etiqueta y título de la sección.
  6. CONTACTO: kicker, título, acento, mensaje, GitHub, LinkedIn, correo y pie.
- Cada lista con filas arrastrables, botón eliminar y "+ AÑADIR".
- Panel derecho sticky con vista previa en miniatura de la landing y aviso
  "Los cambios no son visibles hasta publicar".
- Estados: cargando, guardando, publicado (toast), error de validación.

=========================
10. PUBLICIDAD (#admin/publicidad)
=========================
- Lista de anuncios en tarjetas: preview mini, título, layout, estado
  ACTIVO/INACTIVO, fechas, acciones editar/duplicar/eliminar.
- Botón "NUEVO ANUNCIO +".
- Editor:
  - Campos: título, subtítulo, cuerpo, texto y URL del CTA, URL de imagen.
  - Layout: BANNER / SPLIT / TARJETA (radio cards con miniaturas).
  - Tema: color de fondo, texto y acento con color pickers y campos hex.
  - Interruptor "Anuncio activo".
  - Vista previa en vivo a la derecha, con el mismo componente `.ad` de la
    landing.
- Estado vacío: "No hay publicidad activa" + CTA.
- El anuncio solo se muestra en la landing si está activo.

=========================
11. MÉTRICAS (#admin/metricas)
=========================
- Encabezado "Métricas" + selector de rango: HOY · 7 DÍAS · 30 DÍAS · PERSONALIZADO.
- Cuatro tarjetas KPI: PAGEPVIEWS, SESIONES, VISITANTES ÚNICOS, HOSTS.
  Número grande mono, delta opcional y sparkline SVG.
- Grid de dos paneles:
  - "TRÁFICO POR DÍA": gráfico de líneas/barras con eje y tooltip.
  - "POR RUTA": lista con barra proporcional y valor.
  - "POR HOST": lista con barras.
- Panel "CONSULTA GRAPHQL" con bloque de código y botón "ABRIR GRAPHIQL ↗".
- Estados: cargando (skeleton), sin datos ("Aún no hay tráfico en este rango"),
  error ("Métricas no disponibles") con reintentar, servicio dormido
  ("El servicio está despertando, puede tardar 60 s").
- En móvil: KPIs en 2x2 y paneles apilados.

=========================
12. GENERADOR ESTÁTICO (#admin/generador)
=========================
- Encabezado "Generador estático" y texto breve: convierte un artículo en HTML
  con checksum SHA-256.
- Selector de artículo publicado + botón "GENERAR HTML".
- Durante la generación: consola con líneas animadas:
  "› Validando artículo…", "› Compilando plantilla…", "› Calculando SHA-256…".
- Resultado: tarjeta con estado COMPLETED, build_id, motor (astro), URL del
  artefacto, checksum truncado con botón copiar y botón "ABRIR HTML ↗".
- Historial de builds en tabla.
- Estados: sin artículos, error del generador, HTML no disponible (disco
  efímero) con opción "REGENERAR".

=========================
13. COMPONENTES Y ESTADOS
=========================
Crea una página interna "UI KIT" (puede ser #admin/ui) con:
- Botones: primario, secundario, ghost, peligro, icono, disabled, loading.
- Campos: texto, password, textarea, select, checkbox, radio, toggle, chips,
  color picker, dropzone de imagen, contador.
- Navegación: tabs, sidebar, breadcrumbs, paginación, menú móvil.
- Feedback: badge de estado, toast, modal, tooltip, banner de error,
  skeleton, spinner, estado vacío.
- Datos: tarjeta de artículo, fila de tabla, KPI, terminal, bloque de código.
- Tokens de color y tipografía visibles con sus valores hex.

=========================
14. RESPONSIVE Y ACCESIBILIDAD
=========================
- Diseña a 1440, 1024 y 390 px.
- Nav móvil con menú desplegable; sidebar del CMS como drawer.
- Tablas convertidas en tarjetas en móvil; editor en una sola columna.
- Contrastes AA, foco visible verde de 2px, targets de 44px.
- Todos los formularios con label, ayuda y mensaje de error.
- Respeta prefers-reduced-motion: sin animaciones de entrada en ese caso.

=========================
15. ENTREGABLE
=========================
- Landing y 3 artículos actuales intactos.
- Rutas nuevas navegables entre sí.
- Datos de ejemplo coherentes con el CMS real:
  posts con title, slug, excerpt, content_md, tags, status, reading_time_min,
  published_at, views.
  landing con hero, sections, technologies, projects, certifications, contact.
  ads con title, subtitle, body, cta, image, layout, theme, active.
  métricas con pageviews, sessions, unique visitors, byRoute, byHost.
- Un solo look & feel: parece el mismo producto, no plantillas pegadas.
- Entrega primero el mapa de pantallas y luego implementa en este orden:
  blog público → lector → login → shell → lista → editor → landing →
  publicidad → métricas → generador → UI kit.
```

---

## Notas de implementación

- El CMS real expone `GET /api/v1/landing`, `GET /api/v1/posts`,
  `GET /api/v1/posts/slug/{slug}`, `GET /api/v1/metrics/overview` y
  `POST /api/v1/pages`.
- Los estados 401, 409 (`SLUG_DUPLICATED`), 422 y 429 (`RATE_LIMITED`) deben
  estar diseñados, no solo el camino feliz.
- La consola real ya tiene estas pestañas; el diseño de Figma Make debe
  parecerse a la implementación, no al revés.
