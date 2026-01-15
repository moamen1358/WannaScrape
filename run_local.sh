#!/bin/bash
# Run the scraper API locally without Docker

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🚀 Starting Scraper API (Local)        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed${NC}"
    exit 1
fi

# Check if we're in a conda or virtual environment
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo -e "${GREEN}✅ Using conda environment: $CONDA_DEFAULT_ENV${NC}"
elif [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✅ Using virtual environment: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  No environment detected${NC}"
    echo -e "${YELLOW}   Please activate your conda environment first:${NC}"
    echo -e "${YELLOW}   conda activate scraper_env${NC}"
    echo
    
    # Try to activate conda env if it exists
    if command -v conda &> /dev/null; then
        if conda env list | grep -q "scraper_env"; then
            echo -e "${GREEN}📦 Activating conda scraper_env...${NC}"
            eval "$(conda shell.bash hook)"
            conda activate scraper_env
        fi
    fi
fi

# Check for pydantic-settings
if ! python3 -c "import pydantic_settings" 2>/dev/null; then
    echo -e "${YELLOW}📥 Installing pydantic-settings...${NC}"
    pip install pydantic-settings
fi

# Create necessary directories
echo -e "${GREEN}📁 Creating directories...${NC}"
mkdir -p logs/scrapes screenshots sessions data/logs data/screenshots data/sessions

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use${NC}"
    echo -e "${YELLOW}   Trying port 8001...${NC}"
    PORT=8001
else
    PORT=8000
fi

echo
echo -e "${GREEN}🌐 Starting API on http://0.0.0.0:${PORT}${NC}"
echo -e "${GREEN}📋 Docs at http://localhost:${PORT}/docs${NC}"
echo
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo

# Run the API
uvicorn app.api.scraper_api:app --host 0.0.0.0 --port $PORT --reload
