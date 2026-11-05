FROM python:3.12-slim

WORKDIR /app

# Copiar proyecto
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -e ".[dev]"

# Puerto
EXPOSE 8000

# Variables por defecto (auto permite funcionar standalone en memoria o con MongoDB externo)
ENV APP_ENV=local
ENV APP_MODE=minimal
ENV APP_PORT=8000
ENV STORAGE=auto
ENV MONGO_DB=metrics
ENV BOOTSTRAP_ON_START=true
ENV BEACON_RATE_LIMIT_PER_MINUTE=600

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
