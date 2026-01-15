# Use official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium (dependencies are already in the base image)
RUN playwright install chromium

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/logs/scrapes data/screenshots data/sessions

# Expose port
EXPOSE 8000

# Default command - start the API server
CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
