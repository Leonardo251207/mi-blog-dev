"""Contenido inicial de la landing y de la publicidad.

Se usa para que una instalación nueva (SQLite o MongoDB) tenga algo que
mostrar sin depender de editar HTML. El CMS puede sobrescribirlo desde la
consola: estos valores solo son el punto de partida.

Las claves coinciden con los modelos Pydantic de `schemas.py`.
"""
from __future__ import annotations

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
