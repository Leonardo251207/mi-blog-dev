# Metrics Collector & Retriever (metrics-collector-retriever)

Plataforma privada y autónoma de observación web y analítica respetuosa de la privacidad: captura eventos mediante balizas ligeras (beacons), ingesta tráfico desde edge workers, clasifica visitas de agentes e inteligencias artificiales, emite alertas automáticas (Telegram, Discord, webhooks) y provee superficies de consulta mediante GraphQL y REST.

---

## Características Principales

- **Observación Multi-Sitio Desacoplada:** Trata los dominios como alias dinámicos y los sitios mediante identificadores canónicos (slug).
- **Baliza Universal Ultraligera (/v1/beacon.js):** Script optimizado que no utiliza cookies invasivas y anonimiza IPs mediante hashes con salt.
- **Clasificación Automática de Bots y Agentes de IA:** Detección de rastreadores, indexadores y agentes de IA con almacenamiento de evidencia forense.
- **Doble Superficie de Consulta:**
  - **GraphQL (/v1/query):** Consultas tipadas flexibles con procedencia, nivel de completitud y frescura del dato.
  - **REST (/api/v1/documents/{id}/metrics):** Endpoint de alto rendimiento para pasamanos y lectura analítica instantánea de documentos.
- **Persistencia Flexible (Zero-Setup):** Soporta ejecución en memoria sin infraestructura (STORAGE=memory) o persistencia distribuida en MongoDB (STORAGE=mongo).
- **Sistema de Alertas Antirruido:** Evaluación de reglas de tráfico anómalo con despacho hacia canales de notificación externos.

---

## Instalación y Despliegue

Este repositorio es totalmente autónomo y puede ejecutarse bajo cualquiera de los siguientes 3 escenarios:

### Escenario 1: Python Nativo con Uvicorn (Desarrollo Local)

Ideal para desarrollo local. Por defecto, puede correr en modo memoria sin necesidad de levantar bases de datos externas.

```bash
# 1. Clonar el repositorio y entrar al directorio
git clone <url-del-repositorio> metrics-collector-retriever
cd metrics-collector-retriever

# 2. Crear y activar entorno virtual (Python 3.12+ recomendado)
python -m venv .venv

# En Windows:
.\.venv\Scripts\activate
# En Linux / macOS:
source .venv/bin/activate

# 3. Instalar dependencias en modo editable
pip install -e ".[dev]"

# 4. Configurar variables de entorno iniciales
# En Windows:
Copy-Item .env.example .env
# En Linux / macOS:
cp .env.example .env

# 5. Iniciar el servidor (Puerto 8000 por defecto)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- GraphiQL interactivo: http://localhost:8000/v1/query
- Página de prueba con baliza activa: http://localhost:8000/v1/demo
- Health check: http://localhost:8000/health

---

### Escenario 2: WSLC (Windows Subsystem for Linux Containers)

Construcción y ejecución nativa en contenedores de WSL mediante la herramienta de Microsoft wslc, sin Docker Desktop:

```powershell
# 1. Situarse en la carpeta del repositorio
cd metrics-collector-retriever

# 2. Construir la imagen de contenedor
wslc build -t metrics-collector:latest .

# 3. Opción A: Ejecutar contenedor con almacenamiento en memoria (Zero-Setup)
wslc run -d --name metrics-service -p 8000:8000 -e APP_ENV=local -e STORAGE=memory -e APP_PORT=8000 metrics-collector:latest

# 3. Opción B: Ejecutar con MongoDB en WSLC
# wslc run -d --name mongo -p 27017:27017 mongo:7
# wslc run -d --name metrics-service -p 8000:8000 -e STORAGE=mongo -e MONGO_URI=mongodb://localhost:27017 metrics-collector:latest

# 4. Consultar logs y estado
wslc list
wslc logs metrics-service

# 5. Detener y remover contenedor
wslc stop metrics-service
wslc remove metrics-service
```

---

### Escenario 3: Docker / Docker Compose

Para despliegues basados en contenedores Docker estándar:

#### Usando Docker Compose autónomo (Servicio + MongoDB):
```bash
cd metrics-collector-retriever
docker-compose up -d --build
```

#### Usando Docker CLI directo (Modo Memoria):
```bash
cd metrics-collector-retriever
docker build -t metrics-collector:latest .
docker run -d --name metrics-app -p 8000:8000 -e STORAGE=memory -e APP_ENV=production -e APP_PORT=8000 metrics-collector:latest
```

---

## Configuración y Variables de Entorno

El archivo .env permite controlar los adaptadores de almacenamiento y seguridad:

| Variable | Valor por Defecto | Descripción |
| :--- | :--- | :--- |
| APP_PORT | 8000 | Puerto HTTP donde escucha el servicio |
| APP_ENV | local | Entorno de ejecución (local, production) |
| STORAGE | auto / memory | Adaptador de persistencia: memory (en memoria), mongo (MongoDB) o auto |
| MONGO_URI | mongodb://localhost:27017 | Cadena de conexión al servidor MongoDB si se usa STORAGE=mongo |
| MONGO_DB | metrics | Nombre de la base de datos MongoDB |
| ADMIN_API_KEY | dev-admin-key | Clave requerida en el encabezado X-Admin-Key para mutaciones administrativas |
| IP_HASH_SALT | dev-salt-change-me | Sal secreta utilizada para anonimizar direcciones IP |
| CORS_ORIGINS | * | Orígenes web autorizados para el envío de balizas |

---

## Puertas de Acceso y Endpoints

### Ingesta y Captura
- `GET /v1/beacon.js`: Script JavaScript universal para rastreo en clientes web.
- `POST /v1/collect`: Ingesta masiva de eventos de navegación emitidos por la baliza.
- `POST /v1/collect/edge`: Ingesta de registros y visitas capturadas desde CDNs o edge workers.
- `GET /v1/demo`: Interfaz visual con la baliza inyectada para pruebas de captura en vivo.

### Consulta de Métricas y Analítica
- `GET/POST /v1/query`: Superficie GraphQL para consultas avanzadas de sitios, tráfico, agentes y alertas.
- `GET /api/v1/documents/{document_id}/metrics`: Endpoint REST de pasamanos analítico en tiempo real que entrega métricas clave de documentos (views_total, unique_visitors, avg_dwell_time_sec, bounce_rate_bp, etc.).
- `GET /health`: Endpoint de diagnóstico y salud del servicio.

---

## Pruebas Automatizadas

```bash
cd metrics-collector-retriever
pytest tests -q
```
*Las pruebas utilizan adaptadores mock en memoria y no requieren MongoDB ni servicios externos activos.*

---

## Documentación de Arquitectura

Para un análisis detallado del diseño de dominio y decisiones arquitectónicas:
- [`docs/modelo-conceptual.md`](docs/modelo-conceptual.md): Modelo canónico, dominio, métricas y ADRs.
- [`docs/arquitectura-n-tiers.md`](docs/arquitectura-n-tiers.md): Organización del código por capas y puertos.
- [`docs/snippet-universal.md`](docs/snippet-universal.md): Guía de instalación de la baliza web.
- [`docs/alertas.md`](docs/alertas.md): Configuración de alertas en Telegram y Discord.
