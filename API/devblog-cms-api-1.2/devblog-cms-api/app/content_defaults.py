"""Contenido inicial de la landing y de la publicidad.

Se usa para que una instalación nueva (SQLite o MongoDB) tenga algo que
mostrar sin depender de editar HTML. El CMS puede sobrescribirlo desde la
consola: estos valores solo son el punto de partida.

Las claves coinciden con los modelos Pydantic de `schemas.py`.
"""
from __future__ import annotations

import copy

DEFAULT_LANDING_CONTENT: dict = {
    "hero": {
        "eyebrow": "Hola, mundo",
        "first_name": "Leonardo",
        "last_name": "Nucamendi Ruiz",
        "role": "Estudiante de Ing. en Tecnologías de la Información e Innovación Digital",
        "location": "| México",
        "tagline": "Transformo ideas en soluciones digitales eficientes y escalables.",
        "cta_label": "Ver mis proyectos",
        "cta_url": "#proyectos",
        "note": "Creando desde · México",
        "photo_url": "assets/perfil.jpg",
    },
    "sections": {
        "technologies": {
            "label": "Tecnologías principales",
            "title": "Herramientas y Lenguajes",
        },
        "projects": {
            "label": "Trabajo seleccionado",
            "title": "Proyectos Destacados",
        },
        "certifications": {
            "label": "Conocimiento acreditado",
            "title": "Certificaciones y Credenciales",
        },
        "notes": {
            "label": "Bitácora publicada",
            "title": "Notas y Experimentación",
        },
        "videos": {
            "label": "Multimedia",
            "title": "Videos",
        },
        "contact": {
            "label": "Construyamos algo juntos",
            "title": "¿Tienes una idea?",
        },
    },
    "technologies": [
        {"name": "C++", "icon": "C++", "color": "var(--blue)"},
        {"name": "Java", "icon": "J", "color": "#ff8a3d"},
        {"name": "JavaScript", "icon": "JS", "color": "var(--yellow)"},
        {"name": "Python", "icon": "PY", "color": "var(--purple)"},
        {"name": "HTML", "icon": "</>", "color": "#ff6a55"},
        {"name": "CSS", "icon": "#", "color": "#3da5ff"},
    ],
    "projects": [
        {
            "title": "Lawpocket",
            "badge": "Web",
            "description": "Plataforma de gestión, expedientes y analíticas para despachos de abogados.",
            "url": "https://law-pocket-integrador.vercel.app/index.html",
            "link_label": "Ver web ↗",
            "art": "green",
        },
        {
            "title": "Math & English Quest",
            "badge": "Mobile",
            "description": "App educativa interactiva con sistema de voz y reconocimiento de imágenes para niños.",
            "url": "https://math-english-quest.vercel.app/",
            "link_label": "Ver web ↗",
            "art": "dots",
        },
        {
            "title": "Marketplace Universitario",
            "badge": "En desarrollo",
            "description": "Plataforma comunitaria para intercambio de apuntes y recursos académicos.",
            "url": "",
            "link_label": "",
            "art": "purple",
        },
    ],
    "certifications": [
        {
            "issuer": "Código Facilito",
            "title": "Curso profesional de C++",
            "url": "assets/cert-cpp.pdf",
            "tag": "C++ / 24",
            "color": "var(--green)",
        },
        {
            "issuer": "AWS Academy",
            "title": "AWS Academy Graduate - Cloud Foundations",
            "url": "assets/cert-aws-cloud.pdf",
            "tag": "NUBE / 24",
            "color": "var(--blue)",
        },
        {
            "issuer": "Google",
            "title": "Soporte de sistemas operativos",
            "url": "assets/cert-google-so.pdf",
            "tag": "SO / 24",
            "color": "var(--purple)",
        },
        {
            "issuer": "Cisco Networking Academy",
            "title": "Conceptos básicos de redes",
            "url": "assets/cert-cisco-redes.pdf",
            "tag": "RED / 25",
            "color": "var(--blue)",
        },
        {
            "issuer": "Cisco Networking Academy",
            "title": "Introducción al IoT y Transformación Digital",
            "url": "assets/cert-cisco-iot.pdf",
            "tag": "IOT / 25",
            "color": "var(--green)",
        },
    ],
    "contact": {
        "kicker": "Construyamos algo juntos",
        "title": "¿Tienes una idea?",
        "accent": "Hablemos.",
        "message": "Estoy abierto a proyectos, colaboraciones y oportunidades para seguir aprendiendo.",
        "github": "https://github.com/Leonardo251207",
        "linkedin": "https://www.linkedin.com/in/leonardo-nucamendi-703b48441/",
        "email": "",
        "footer": "© 2025 Leonardo Nucamendi — creado con intención",
    },
}

DEFAULT_ADS: list[dict] = [
    {
        "title": "Disponible para nuevos proyectos",
        "subtitle": "Desarrollo web · apps · automatización",
        "body": "¿Tienes una idea o necesitas apoyo con tu proyecto? Hablemos.",
        "cta_label": "Escríbeme",
        "cta_url": "#contacto",
        "image_url": "",
        "layout": "banner",
        "theme": {
            "background": "#0b1110",
            "text": "#eef5f1",
            "accent": "#3df0a8",
        },
        "active": True,
    }
]

# ============================== SITIOS =======================================
# Un sitio es una landing administrable. El CMS reutiliza el mismo editor y el
# mismo renderer para todos; solo cambia el contenido y el tema.
DEFAULT_THEME_PORTFOLIO = {
    "preset": "tech-terminal",
    "accent": "#3df0a8",
    "background": "#050807",
    "surface": "#0b1110",
    "text": "#eef5f1",
    "muted": "#8c9c95",
    "heading_font": "Manrope",
    "body_font": "Manrope",
    "radius": 0,
}

DEFAULT_THEME_PROJECT = {
    **DEFAULT_THEME_PORTFOLIO,
    "preset": "editorial-minimal",
    "accent": "#3de4ff",
}

DEFAULT_THEME_CLIENT = {
    **DEFAULT_THEME_PORTFOLIO,
    "preset": "modern-magazine",
    "accent": "#b48cff",
}

DEFAULT_SITES: list[dict] = [
    {
        "site_id": "portfolio",
        "name": "Leonardo Nucamendi · Portafolio",
        "kind": "portfolio",
        "domain": "mi-landing-devblog.vercel.app",
        "description": "Landing profesional con proyectos, certificaciones y contacto.",
        "status": "active",
        "theme": copy.deepcopy(DEFAULT_THEME_PORTFOLIO),
    },
    {
        "site_id": "devblog-project",
        "name": "Proyecto DevBlog_",
        "kind": "project",
        "domain": "mi-landing-devblog.vercel.app/sitio.html?site=devblog-project",
        "description": "Caso de estudio del CMS, blog, métricas y generador estático.",
        "status": "active",
        "theme": copy.deepcopy(DEFAULT_THEME_PROJECT),
    },
    {
        "site_id": "devblog",
        "name": "DevBlog_ · Blog",
        "kind": "blog",
        "domain": "mi-blog-dev.vercel.app",
        "description": "Sitio del blog y su landing de bienvenida.",
        "status": "active",
        "theme": copy.deepcopy(DEFAULT_THEME_PORTFOLIO),
    },
]


def _project_landing() -> dict:
    content = copy.deepcopy(DEFAULT_LANDING_CONTENT)
    content["hero"] = {
        "eyebrow": "Proyecto · Blog Dev",
        "first_name": "Proyecto",
        "last_name": "DevBlog_",
        "role": "CMS API-First + blog + métricas + generador estático",
        "location": "| México",
        "tagline": "Un ecosistema completo para publicar, medir y compilar contenido.",
        "cta_label": "Ver el blog",
        "cta_url": "https://mi-blog-dev.vercel.app/",
        "note": "Caso de estudio · 2026",
        "photo_url": "",
    }
    content["sections"]["technologies"] = {
        "label": "Stack del proyecto",
        "title": "Tecnologías que lo hacen posible",
    }
    content["sections"]["projects"] = {
        "label": "Módulos del ecosistema",
        "title": "Arquitectura y funcionalidades",
    }
    content["sections"]["certifications"] = {"label": "", "title": ""}
    content["sections"]["notes"] = {"label": "Bitácora", "title": "Notas del proyecto"}
    content["sections"]["videos"] = {"label": "Demostración", "title": "Recorrido en video"}
    content["technologies"] = [
        {"name": "Python", "icon": "PY", "color": "var(--purple)"},
        {"name": "FastAPI", "icon": "API", "color": "var(--green)"},
        {"name": "MongoDB", "icon": "DB", "color": "#3df0a8"},
        {"name": "JavaScript", "icon": "JS", "color": "var(--yellow)"},
        {"name": "Render", "icon": "R", "color": "var(--cyan)"},
        {"name": "Vercel", "icon": "V", "color": "var(--text)"},
    ]
    content["projects"] = [
        {
            "title": "CMS API",
            "badge": "FastAPI",
            "description": "Borradores, publicación, landing editable, publicidad y métricas.",
            "url": "https://devblog-cms-leonardo.onrender.com/docs",
            "link_label": "Ver API ↗",
            "art": "green",
        },
        {
            "title": "Blog DevBlog_",
            "badge": "Web",
            "description": "Portada dinámica y lector de artículos por slug desde el CMS.",
            "url": "https://mi-blog-dev.vercel.app/",
            "link_label": "Abrir blog ↗",
            "art": "dots",
        },
        {
            "title": "Generador estático",
            "badge": "Astro",
            "description": "Convierte artículos publicados en HTML con checksum SHA-256.",
            "url": "https://devblog-generator-leonardo.onrender.com/docs",
            "link_label": "Ver generador ↗",
            "art": "purple",
        },
    ]
    content["certifications"] = []
    content["videos"] = [
        {
            "title": "Recorrido del CMS",
            "description": "Demostración del dashboard, el editor y la publicación de contenido.",
            "url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
            "poster": "",
            "captions_url": "",
            "cta_label": "",
            "cta_url": "",
            "aspect": "16:9",
        }
    ]
    content["contact"] = {
        "kicker": "¿Construimos algo juntos?",
        "title": "Este proyecto",
        "accent": "puede ser el tuyo.",
        "message": "Si necesitas un CMS, una landing o un blog administrable, hablemos.",
        "github": "https://github.com/Leonardo251207",
        "linkedin": "https://www.linkedin.com/in/leonardo-nucamendi-703b48441/",
        "email": "",
        "footer": "© 2026 Leonardo Nucamendi — creado con intención",
    }
    return content


def _blog_landing() -> dict:
    content = copy.deepcopy(DEFAULT_LANDING_CONTENT)
    content["hero"] = {
        "eyebrow": "Bitácora publicada",
        "first_name": "Notas y",
        "last_name": "Experimentación",
        "role": "Apuntes de desarrollo, datos y despliegue",
        "location": "| DevBlog_",
        "tagline": "Todo lo que publico nace en el CMS, se mide y puede compilarse como HTML estático.",
        "cta_label": "Leer el blog",
        "cta_url": "https://mi-blog-dev.vercel.app/",
        "note": "CMS API-First",
        "photo_url": "",
    }
    content["sections"]["technologies"] = {"label": "", "title": ""}
    content["sections"]["projects"] = {"label": "", "title": ""}
    content["sections"]["certifications"] = {"label": "", "title": ""}
    content["sections"]["notes"] = {"label": "Publicaciones", "title": "Últimas entradas"}
    content["sections"]["videos"] = {"label": "", "title": ""}
    content["technologies"] = []
    content["projects"] = []
    content["certifications"] = []
    content["videos"] = []
    content["contact"] = {
        **copy.deepcopy(DEFAULT_LANDING_CONTENT["contact"]),
        "kicker": "Del blog al portafolio",
        "title": "Mira el",
        "accent": "portafolio.",
        "message": "Proyectos, certificaciones y la persona detrás de estas notas.",
        "footer": "© 2026 Leonardo Nucamendi — creado con intención",
    }
    return content


def _client_landing() -> dict:
    content = copy.deepcopy(DEFAULT_LANDING_CONTENT)
    content["hero"] = {
        "eyebrow": "Nuevo sitio",
        "first_name": "Tu",
        "last_name": "Marca",
        "role": "Landing administrable desde el CMS",
        "location": "",
        "tagline": "Una base lista para personalizar sin reconstruir el CMS.",
        "cta_label": "Contacto",
        "cta_url": "#contacto",
        "note": "Configuración mínima",
        "photo_url": "",
    }
    content["sections"]["technologies"] = {"label": "", "title": ""}
    content["sections"]["projects"] = {"label": "Servicios", "title": "Lo que ofrecemos"}
    content["sections"]["certifications"] = {"label": "", "title": ""}
    content["sections"]["notes"] = {"label": "", "title": ""}
    content["sections"]["videos"] = {"label": "Video", "title": "Conoce el proyecto"}
    content["technologies"] = []
    content["projects"] = []
    content["certifications"] = []
    content["videos"] = []
    content["contact"] = {
        **copy.deepcopy(DEFAULT_LANDING_CONTENT["contact"]),
        "kicker": "Hablemos",
        "title": "¿Tienes una idea?",
        "accent": "Hagámosla realidad.",
        "message": "Cuéntame qué necesitas y lo aterrizamos juntos.",
        "github": "",
        "linkedin": "",
        "email": "",
        "footer": "© 2026 · Sitio administrado con DevBlog_ CMS",
    }
    return content


def landing_default_for(site_id: str, kind: str = "client") -> dict:
    if site_id == "devblog-project" or kind == "project":
        return _project_landing()
    if site_id == "devblog" or kind == "blog":
        return _blog_landing()
    if kind == "portfolio" or site_id == "portfolio":
        return copy.deepcopy(DEFAULT_LANDING_CONTENT)
    return _client_landing()
