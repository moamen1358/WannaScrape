#!/usr/bin/env python3
"""
Web Scraper - Production-Ready Article Extraction

A professional web scraper with advanced anti-detection features.

Usage:
    python main.py scrape <url>              # Scrape a single URL
    python main.py scrape <url> --no-headless   # Visible browser mode
    python main.py search "<text>"           # Find source of text
    python main.py serve                     # Start API server
    python main.py serve --port 8080         # Custom port
    python main.py stats                     # Show statistics
    python main.py version                   # Show version

For more help:
    python main.py --help
    python main.py scrape --help
"""

import sys
import os

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure directories exist
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/screenshots", exist_ok=True)
os.makedirs("data/sessions", exist_ok=True)


def main():
    """Main entry point."""
    try:
        from app.cli.commands import app
        app()
    except ImportError as e:
        # Fallback for missing dependencies
        print(f"Error: Missing dependencies. {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
