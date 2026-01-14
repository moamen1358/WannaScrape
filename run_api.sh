#!/bin/bash

# Activate conda scraper_env environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate scraper_env

# Kill any existing uvicorn processes to avoid port conflicts
pkill -f uvicorn

echo "Starting Scraper API on port 8000..."
python -m uvicorn app.api.scraper_api:app --host 0.0.0.0 --port 8000 > logs/scraper.log 2>&1 &

echo "Starting Search API on port 8001..."
python -m uvicorn app.api.search_api:app --host 0.0.0.0 --port 8001 > logs/search.log 2>&1 &

echo "Services started!"
echo "Scraper API: http://localhost:8000/docs"
echo "Search API:  http://localhost:8001/docs"
echo "Logs are being written to logs/scraper.log and logs/search.log"
echo "Press Ctrl+C to stop both services."

# Wait for user to press Ctrl+C
trap "kill 0" EXIT
wait
