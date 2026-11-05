"""Carga los tres artículos de ejemplo en la base SQLite.

Uso (desde la carpeta del proyecto de la API):

    python -m app.seed

Es idempotente: si un slug ya existe, no lo duplica. Sirve para que el blog
tenga contenido la primera vez que se conecta a la API.
"""
from __future__ import annotations

from .config import load_settings
from .repository_factory import build_repository
from .schemas import DraftCreate
from .services import PostService

ARTICLES: list[dict] = [
    {
        "title": "Despliega tu web gratis en Vercel",
        "slug": "despliega-tu-web-gratis-en-vercel",
        "tags": ["tutorial", "deployment"],
        "content": """## Antes de desplegar

Publicar un portafolio en Vercel es rápido si llegas con el trabajo ordenado. Esta es la lista que uso antes de cada despliegue.

- `index.html` en la raíz del proyecto.
- Enlaces relativos probados en local.
- Repositorio sincronizado en GitHub.

## Flujo de despliegue

1. Sube los cambios con `git push origin main`.
2. Importa el repositorio desde el panel de Vercel.
3. Revisa el comando de build y el directorio de salida.
4. Publica y comprueba la URL asignada.

```bash
git add .
git commit -m "Preparar despliegue"
git push origin main
```

> Consejo: si el proyecto es estático, Vercel no necesita comando de build.

La primera vez parece un trámite largo; después son tres pasos y un café.
""",
    },
    {
        "title": "Prompts de IA para dominar C++",
        "slug": "prompts-de-ia-para-dominar-cpp",
        "tags": ["estudio", "c-plus-plus"],
        "content": """## Por qué usar prompts

Un buen prompt no reemplaza el estudio: lo acelera. La clave es pedir contexto, un ejemplo seguro y los errores típicos.

## Tres prompts que funcionan

1. **Explicar punteros**: pide una analogía visual y un ejemplo seguro.
2. **Corregir un segmentation fault**: pide la causa y una solución con gestión de memoria.
3. **Optimizar copias**: pide referencias constantes y el impacto en memoria.

```cpp
int valor = 42;
int* puntero = &valor;
std::cout << *puntero;
```

> Un puntero no es el valor: es la dirección donde vive el valor.

## Cómo verificar la respuesta

Compila el ejemplo, ejecútalo con un caso pequeño y compara con la documentación. Si la IA no explica por qué funciona, todavía no terminaste.
""",
    },
    {
        "title": "Reconocimiento de voz en apps móviles",
        "slug": "reconocimiento-de-voz-en-apps-moviles",
        "tags": ["desarrollo", "apps"],
        "content": """## El problema

En Math & English Quest necesitábamos que los niños practicaran pronunciación sin depender de un teclado. La app debía escuchar, comparar y responder con voz.

## Flujo de reconocimiento

1. El niño mantiene presionado el botón y pronuncia la palabra.
2. `SpeechRecognizer` captura el audio y devuelve el texto reconocido.
3. La app compara con la palabra objetivo y calcula una coincidencia.
4. La retroalimentación se explica con `SpeechSynthesis`.

```kotlin
val recognizer = SpeechRecognizer
  .createSpeechRecognizer(context)
recognizer.setRecognitionListener(listener)
recognizer.startListening(intent)
```

## Lo que aprendí

- El silencio también es información: hay que manejar el timeout.
- La retroalimentación debe ser inmediata y amable.
- Probar con voces y acentos distintos cambia por completo el resultado.

> La tecnología educativa funciona cuando el error se siente como parte del juego.
""",
    },
]


def main() -> None:
    settings = load_settings()
    repo = build_repository(settings)
    service = PostService(repo, settings.cursor_secret)
    try:
        for article in ARTICLES:
            if repo.get_by_slug(article["slug"]) is not None:
                print(f"= {article['slug']} (ya existe)")
                continue
            draft = service.create_draft(DraftCreate(**article))
            published = service.publish(draft.post_id)
            print(f"+ {published.slug} -> {settings.article_url(published.slug)}")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
