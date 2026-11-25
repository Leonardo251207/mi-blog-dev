<div align="center">

<img src="docs/banner.svg" alt="DevBlog_ — CMS, blog, landings y métricas" width="100%">

<br>

<a href="https://mi-landing-devblog.vercel.app/">
  <img src="https://img.shields.io/badge/Portafolio-Live-3df0a8?style=for-the-badge&logo=vercel&logoColor=0b0f0e" alt="Portafolio">
</a>
<a href="https://mi-blog-dev.vercel.app/">
  <img src="https://img.shields.io/badge/Blog-Live-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Blog">
</a>
<a href="https://devblog-cms-leonardo.onrender.com/docs">
  <img src="https://img.shields.io/badge/CMS%20API-Swagger-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="CMS API">
</a>
<a href="https://devblog-metrics-leonardo.onrender.com/v1/query">
  <img src="https://img.shields.io/badge/GraphQL-GraphiQL-E10098?style=for-the-badge&logo=graphql&logoColor=white" alt="GraphQL">
</a>
<a href="https://devblog-generator-leonardo.onrender.com/docs">
  <img src="https://img.shields.io/badge/Generator-Swagger-3df0a8?style=for-the-badge&logo=python&logoColor=0b0f0e" alt="Generator">
</a>
<a href="#pruebas">
  <img src="https://img.shields.io/badge/Tests-81%20passed-0b0f0e?style=for-the-badge&logo=pytest&logoColor=3df0a8" alt="81 tests">
</a>

# DevBlog_

**CMS API-First + blog + landings multi-sitio + métricas GraphQL + generador estático.**

Proyecto de Aplicaciones Web construido con FastAPI, MongoDB Atlas, Render,
Vercel y GitHub Pages.

[Portafolio](https://mi-landing-devblog.vercel.app/) ·
[Blog](https://mi-blog-dev.vercel.app/) ·
[Consola CMS](https://mi-blog-dev.vercel.app/admin.html) ·
[API](https://devblog-cms-leonardo.onrender.com/docs)

</div>

---

## Demo en vivo

| Recurso | URL |
|---|---|
| Portafolio | <https://mi-landing-devblog.vercel.app/> |
| Landing del proyecto | <https://mi-landing-devblog.vercel.app/sitio.html?site=devblog-project> |
| Blog | <https://mi-blog-dev.vercel.app/> |
| Consola CMS | <https://mi-blog-dev.vercel.app/admin.html> |
| CMS API / Swagger | <https://devblog-cms-leonardo.onrender.com/docs> |
| Métricas / GraphiQL | <https://devblog-metrics-leonardo.onrender.com/v1/query> |
| Generador / Swagger | <https://devblog-generator-leonardo.onrender.com/docs> |

## Arquitectura

```mermaid
flowchart LR
  subgraph Cliente
    B["Blog<br/>Vercel / GitHub Pages"]
    L["Landings multi-sitio<br/>portafolio · proyecto · clientes"]
    A["Consola CMS<br/>blog · sitios · landing"]
  end

  subgraph Render
    C["CMS API<br/>FastAPI + Bearer"]
    M["Metrics + GraphQL<br/>beacon y consultas"]
    G["Static Generator<br/>HTML + SHA-256"]
  end

  D[("MongoDB Atlas")]

  B -->|REST /api/v1| C
  B -->|beacon /v1/collect| M
  L -->|sites /api/v1| C
  L -->|beacon /v1/collect| M
  A -->|CRUD /api/v1| C
  A -->|POST /api/v1/pages| G
  C --> D
  M --> D
```

## Módulos

| Módulo | Capacidades |
|---|---|
| **CMS API** | Posts y borradores, sitios, landings, publicidad, media y métricas. UUIDv7, slugs, cursores, idempotencia, rate limit, ETag/304 y errores uniformes. |
| **Blog** | Portada dinámica, artículo por slug, Markdown seguro, vistas y respaldo estático. |
| **Multi-sitio** | Portafolio, landing del proyecto, blog y landings de clientes con contenido, tema y publicación independientes. |
| **Videos** | URL o archivo subido (MP4/WebM/MOV, 25 MB), póster, subtítulos VTT, YouTube/Vimeo y CTA. |
| **Consola CMS** | Dashboard, sitios, editor con portada/SEO/tipografía/índice, publicidad, métricas y exportación Markdown/JSON. |
| **Métricas** | Beacon, pageviews, sesiones, visitantes únicos, rutas, hosts y consultas GraphQL. |
| **Generador** | HTML estático a partir de una instantánea del artículo, con checksum SHA-256. |

## API principal

| Área | Endpoints |
|---|---|
| Blog | `GET /api/v1/posts`, `GET /api/v1/posts/slug/{slug}`, `POST /api/v1/posts/{id}/views` |
| CMS | `GET/POST /api/v1/drafts`, `GET/PUT/DELETE /api/v1/drafts/{id}`, `POST /api/v1/drafts/{id}/publish` |
| Sitios | `GET /api/v1/sites`, `GET /api/v1/sites/{site_id}/landing`, `PUT /api/v1/sites/{site_id}/landing/draft` |
| Landing | `GET /api/v1/landing`, `GET /api/v1/ads`, `GET /api/v1/metrics/overview` |
| Media | `POST /api/v1/media`, `GET /api/v1/media/{media_id}` |
| Generador | `POST /api/v1/pages` en el servicio de generación |

## Estructura

```text
mi-blog-dev/
├── API/devblog-cms-api-1.2/devblog-cms-api/   # CMS FastAPI
├── dev-blog/                                  # Blog, consola y assets del CMS
├── pendiente/
│   ├── metrics-navigation-main/               # Colector de métricas + GraphQL
│   └── static-sites-generator-main/           # Generador estático
├── docs/banner.svg
├── render.yaml
├── setup.ps1
├── start-all.ps1
└── README.md
```

## Stack

`Python 3.12` · `FastAPI` · `Pydantic` · `MongoDB Atlas` / `SQLite` ·
`JavaScript vanilla` · `Render` · `Vercel` · `GitHub Pages` · `GitHub Actions`

## Pruebas

| Suite | Resultado |
|---|---|
| CMS (contrato + Mongo + contenido + sitios + media) | **64 / 64** |
| Métricas | **13 / 13** |
| Generador estático | **4 / 4** |
| **Total** | **81 / 81** |

## Autor

**Leonardo Nucamendi Ruiz**  
Estudiante de Ing. en Tecnologías de la Información e Innovación Digital · México

[GitHub](https://github.com/Leonardo251207) ·
[LinkedIn](https://www.linkedin.com/in/leonardo-nucamendi-703b48441/) ·
[Portafolio](https://mi-landing-devblog.vercel.app/)

---

<div align="center">
  <sub>Hecho con intención · 2026</sub>
</div>
