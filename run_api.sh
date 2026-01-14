#!/bin/bash

# =============================================================================
# Web Scraper API Launcher
# =============================================================================
# Starts the scraper and search APIs with enterprise logging
# Logs are automatically written to logs/ directory in JSON format
# =============================================================================

set -e

# Configuration
SCRAPER_PORT=${SCRAPER_PORT:-8000}
SEARCH_PORT=${SEARCH_PORT:-8001}
ENVIRONMENT=${ENVIRONMENT:-development}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Export for the application
export ENVIRONMENT
export LOG_LEVEL

# Activate conda environment if available
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate scraper_env 2>/dev/null || true
fi

# Create logs directory
mkdir -p logs

# Kill any existing uvicorn processes
pkill -f "uvicorn app.api" 2>/dev/null || true
sleep 1

echo "============================================="
echo "  Web Scraper API - Enterprise Edition"
echo "============================================="
echo "Environment: $ENVIRONMENT"
echo "Log Level:   $LOG_LEVEL"
echo "---------------------------------------------"

# Start Scraper API
echo "Starting Scraper API on port $SCRAPER_PORT..."
python -m uvicorn app.api.scraper_api:app \
    --host 0.0.0.0 \
    --port $SCRAPER_PORT \
    --log-level warning &
SCRAPER_PID=$!

# Start Search API
echo "Starting Search API on port $SEARCH_PORT..."
python -m uvicorn app.api.search_api:app \
    --host 0.0.0.0 \
    --port $SEARCH_PORT \
    --log-level warning &
SEARCH_PID=$!

sleep 2

echo "---------------------------------------------"
echo "Services running:"
echo "  Scraper API: http://localhost:$SCRAPER_PORT/docs"
echo "  Search API:  http://localhost:$SEARCH_PORT/docs"
echo "  Health:      http://localhost:$SCRAPER_PORT/health"
echo "  Stats:       http://localhost:$SCRAPER_PORT/stats"
echo "---------------------------------------------"
echo "Logs (JSON format):"
echo "  logs/web-scraper-api.json.log"
echo "---------------------------------------------"
echo "Press Ctrl+C to stop"

# Handle shutdown
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $SCRAPER_PID $SEARCH_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
