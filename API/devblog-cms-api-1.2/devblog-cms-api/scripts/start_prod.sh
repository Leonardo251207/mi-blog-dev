#!/usr/bin/env sh
# Arranque de producción del CMS: crea/verifica datos iniciales y levanta Uvicorn.
set -e

if [ "${CMS_SEED_ON_START:-true}" = "true" ]; then
    python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
