# Static Pages Generator (static_pages_generator)

Worker autónomo de compilación estática y repositorio de entrega de artefactos web para arquitecturas headless y desacopladas. Diseñado bajo Vertical Slice Architecture y Puertos y Adaptadores (Arquitectura Hexagonal).

---

## Rol en el Ecosistema

Conforme a la especificación de arquitectura, este servicio actúa como Consumidor / Worker:
- Recibe instantáneas inmutables de documentos publicados (frozen_template, canvas_blocks, metadata_values).
- Responde sincrónicamente (201 Created) para compilaciones rápidas (< 10s) o asíncronamente (202 Accepted) para trabajos pesados.
- Gestiona la integridad criptográfica (SHA-256) de los artefactos y su auto-reparación a partir de snapshots.
- Puerto de servicio estándar: 8001 (coexiste con CMS en 8080 y Métricas en 8000).

---

## Características Principales

- **Arquitectura Hexagonal + Vertical Slices:** Separación modular en rebanadas funcionales autosuficientes (generate_sources, compile_artifact, manage_artifacts).
- **Soporte Multi-Motor (Pluggable SSG):** Capacidad para compilar estructuras intermedias a motores estáticos modernos como Astro, Hugo y Quarto.
- **Doble Modo Operativo (SLA Dinámico):**
  - Sincrónico (201 Created): Retorna el artefacto terminado en menos de 10 segundos.
  - Asíncrono (202 Accepted): Procesa compilaciones extensas en background retornando un identificador de seguimiento (build_id).
- **Garantía de Integridad Criptográfica (SHA-256):** Cada artefacto compilado es verificado con hash criptográfico y validado contra disco.
- **Auto-Recuperación de Artefactos:** Si un archivo HTML físico se pierde o corrompe en disco, el endpoint de servicio lo reconstruye de forma transparente utilizando el snapshot original.
- **Autonomía Total:** Almacenamiento local mediante SQLite y carpetas de artefactos sin requerir bases de datos pesadas externas.

---

## Instalación y Despliegue

Este repositorio es totalmente autónomo y puede ejecutarse bajo cualquiera de los siguientes 3 escenarios:

### Escenario 1: Python Nativo con Uvicorn (Desarrollo Local)

Ideal para desarrollo local y ejecución directa sobre el sistema operativo host.

```bash
# 1. Clonar el repositorio y entrar al directorio
git clone <url-del-repositorio> static-pages-generator
cd static-pages-generator

# 2. Crear y activar entorno virtual
python -m venv venv

# En Windows:
.\venv\Scripts\activate
# En Linux / macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar el servidor (Puerto 8001 por defecto)
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

- Swagger UI interactivo: http://localhost:8001/docs
- Health check: http://localhost:8001/health

---

### Escenario 2: WSLC (Windows Subsystem for Linux Containers)

Permite construir y ejecutar el contenedor directamente mediante el CLI nativo de Microsoft wslc, sin necesidad de instalar Docker Desktop ni daemons adicionales:

```powershell
# 1. Situarse en la carpeta del repositorio
cd static-pages-generator

# 2. Construir la imagen de contenedor
wslc build -t static-pages-generator:latest .

# 3. Ejecutar el contenedor en segundo plano (puerto 8001)
wslc run -d --name static-worker -p 8001:8001 -e PORT=8001 static-pages-generator:latest

# 4. Monitorear logs y estado
wslc list
wslc logs static-worker

# 5. Detener y remover contenedor
wslc stop static-worker
wslc remove static-worker
```

---

### Escenario 3: Docker / Docker Compose

Para despliegues estándar basados en contenedores OCI:

#### Usando Docker CLI directo:
```bash
# Construir imagen
docker build -t static-pages-generator:latest .

# Ejecutar contenedor persistiendo artefactos y datos
docker run -d --name static-service \
  -p 8001:8001 \
  -e PORT=8001 \
  -v $(pwd)/dist:/app/dist \
  -v $(pwd)/data:/app/data \
  static-pages-generator:latest
```

#### Usando Docker Compose autónomo:
```bash
docker-compose up -d --build
```

---

## Configuración y Variables de Entorno

| Variable | Valor por Defecto | Descripción |
| :--- | :--- | :--- |
| PORT | 8001 | Puerto HTTP donde escucha el servicio |
| HOST | 0.0.0.0 | Interfaz de enlace de red |
| DATA_DIR | ./data | Directorio para base de datos SQLite y registros |
| STORAGE_DIR | ./dist | Directorio de almacenamiento de artefactos finales generados |
| SOURCES_DIR | ./sources | Directorio donde se generan los archivos fuente temporales |
| TEMPLATES_DIR | ./templates | Directorio de plantillas base de los motores estáticos |
| SQLITE_DB_PATH | ./data/data.db | Ruta del archivo de base de datos SQLite |

---

## Catálogo de la API REST

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| POST | /api/v1/pages | Recibe la instantánea del documento (bloques, metadata, layout). Genera fuentes y compila el artefacto HTML. Retorna 201 Created (sincrónico) o 202 Accepted (asíncrono). |
| GET | /api/v1/pages/{id} | Retorna el estado del artefacto, checksum SHA-256, URL de salida y metadata de compilación. |
| GET | /api/v1/pages/{id}/content | Sirve el contenido HTML final del artefacto compilado. Si el archivo físico falta en disco, ejecuta auto-recuperación transparente desde el snapshot. |
| GET | /api/v1/pages/{id}/verify | Valida la integridad criptográfica en disco contra la base de datos (SHA-256), permitiendo reparación manual o automática (?auto_repair=true). |
| POST | /api/v1/pages/{id}/rebuild | Fuerza una recompilación limpia del sitio web utilizando la instantánea original inmutable. |
| GET | /api/v1/builds/{id} | Consulta el progreso y estado de un trabajo de compilación en segundo plano (PENDING, PROCESSING, COMPLETED, FAILED). |
| GET | /health | Diagnóstico de salud operativo del servicio. |

---

## Pruebas Automatizadas

```bash
# Ejecutar suite con pytest
pytest tests -v

# Ejecutar pruebas con unittest nativo
python -m unittest tests/test_api.py

# Script de prueba de generación multilínea
python generate_via_api.py
```
