# wannaScrape - Stealth Web Scraper API
# Production-ready with anti-detection features
#
# Volume Mounts (for persistent data):
#   - /app/data   -> Logs, screenshots, session data
#   - /app/config -> Configuration files (config.json, proxies.txt)
#
# Example docker run:
#   docker run -d -p 8000:8000 \
#     -v ./data:/app/data \
#     -v ./config:/app/config \
#     moamen1358/wannascrape:latest

FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Metadata
LABEL org.opencontainers.image.title="wannaScrape"
LABEL org.opencontainers.image.description="Production-ready web scraper with anti-detection features"
LABEL org.opencontainers.image.version="2.0.0"
LABEL org.opencontainers.image.vendor="moamen1358"
LABEL org.opencontainers.image.source="https://github.com/moamen1358/Search_news_and_scrape_them"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV APP_NAME=wannascrape
ENV APP_VERSION=2.0.0

# Configure data and config directories (can be overridden)
ENV WANNASCRAPE_DATA_DIR=/app/data
ENV WANNASCRAPE_CONFIG_DIR=/app/config

# Set work directory
WORKDIR /app

# Install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium
RUN playwright install chromium

# Copy application code
COPY . .

# Create data and config directories with proper structure
# These will be overwritten by volume mounts if provided
RUN mkdir -p /app/data/logs/scrapes /app/data/screenshots /app/data/sessions /app/config

# Declare volumes for persistent data
VOLUME ["/app/data", "/app/config"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command - start the API server
CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
