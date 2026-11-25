# DevBlog CMS API (v1.2)

Implementación en **FastAPI** del contrato API-First del proyecto DevBlog_.
Gestiona blog, sitios y landings, publicidad, archivos multimedia y métricas.

## Alcance

- Posts y borradores con publicación, slugs únicos y paginación por cursor.
- Sitios multi-landing con contenido, tema, borrador y publicación por sitio.
- Landing editable (hero, proyectos, tecnologías, certificaciones, videos y contacto).
- Publicidad configurable con layouts y tema.
- Archivos multimedia para videos e imágenes.
- Resumen de métricas consultado por GraphQL desde el backend.
- CORS, rate limit, ETag/304, idempotencia y errores uniformes.
- Persistencia SQLite en local y MongoDB Atlas en producción.

## Endpoints principales

| Área | Rutas |
|---|---|
| Posts | `/api/v1/posts`, `/api/v1/posts/slug/{slug}`, `/api/v1/posts/{id}/views` |
| Borradores | `/api/v1/drafts`, `/api/v1/drafts/{id}`, `/api/v1/drafts/{id}/publish` |
| Sitios | `/api/v1/sites`, `/api/v1/sites/{site_id}/landing` |
| Landing | `/api/v1/landing`, `/api/v1/landing/draft`, `/api/v1/landing/publish` |
| Publicidad | `/api/v1/ads`, `/api/v1/ads/admin` |
| Media | `/api/v1/media`, `/api/v1/media/{media_id}` |
| Métricas | `/api/v1/metrics/overview` |

La documentación interactiva está disponible en `/docs`.

## Persistencia

- **Local:** SQLite (`data/devblog.db`).
- **Producción:** MongoDB Atlas (`CMS_MONGO_URI`).
- Los archivos de media se guardan en SQLite local o MongoDB GridFS.

## Pruebas

```text
64 passed
```

El contrato y el Anexo D de implementación están en:

- [`Especificacion_API_CMS_DevBlog_v1.2_implementacion.docx`](../../Especificacion_API_CMS_DevBlog_v1.2_implementacion.docx)
- [`Especificacion_API_CMS_DevBlog_v1.2_implementacion.pdf`](../../Especificacion_API_CMS_DevBlog_v1.2_implementacion.pdf)
