#!/bin/bash

# =============================================================================
# Docker Entrypoint
# =============================================================================
# Enterprise logging writes to /app/logs/ automatically
# Set SERVICE_TYPE=scraper or SERVICE_TYPE=search
# =============================================================================

set -e

SERVICE_TYPE=${SERVICE_TYPE:-scraper}
ENVIRONMENT=${ENVIRONMENT:-production}
LOG_LEVEL=${LOG_LEVEL:-INFO}

export ENVIRONMENT
export LOG_LEVEL

mkdir -p /app/logs

echo "Starting $SERVICE_TYPE service (env: $ENVIRONMENT)"

if [ "$SERVICE_TYPE" = "scraper" ]; then
    exec uvicorn app.api.scraper_api:app --host 0.0.0.0 --port 8000
elif [ "$SERVICE_TYPE" = "search" ]; then
    exec uvicorn app.api.search_api:app --host 0.0.0.0 --port 8001
else
    echo "Unknown SERVICE_TYPE: $SERVICE_TYPE (use 'scraper' or 'search')"
    exit 1
fi
