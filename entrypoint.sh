#!/bin/bash

# Set default service type if not provided
SERVICE_TYPE=${SERVICE_TYPE:-scraper}

if [ "$SERVICE_TYPE" = "scraper" ]; then
    echo "Starting Scraper API on port 8000..."
    # Run uvicorn and pipe output to both stdout (for docker logs) and the log file
    uvicorn app.api.scraper_api:app --host 0.0.0.0 --port 8000 2>&1 | tee -a /app/logs/scraper.log
elif [ "$SERVICE_TYPE" = "search" ]; then
    echo "Starting Search API on port 8001..."
    # Run uvicorn and pipe output to both stdout (for docker logs) and the log file
    uvicorn app.api.search_api:app --host 0.0.0.0 --port 8001 2>&1 | tee -a /app/logs/search.log
else
    echo "Unknown SERVICE_TYPE: $SERVICE_TYPE"
    exit 1
fi
