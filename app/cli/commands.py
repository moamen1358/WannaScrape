"""
CLI commands for the web scraper using Typer.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from app.core import WebScraper
from app.logging import setup_logging
from app.config.settings import get_config_dir

app = typer.Typer(
    name="scraper",
    help="Professional Web Scraper & Article Extractor with anti-detection",
    add_completion=False,
)
console = Console()


def show_result(result: dict, format: str = "pretty"):
    """Display scrape result."""
    if format == "json":
        console.print_json(data=result)
        return

    if "error" in result:
        console.print(Panel(
            f"[red]Error:[/red] {result['error']}\n"
            f"[dim]Type: {result.get('error_type', 'unknown')}[/dim]\n"
            f"[dim]URL: {result.get('final_url', 'N/A')}[/dim]",
            title="❌ Scrape Failed",
            border_style="red"
        ))
    else:
        title = result.get("title", "Untitled")
        text = result.get("text", "")
        source = result.get("source", result.get("final_url", ""))
        date = result.get("date", "Unknown")

        # Truncate text for display
        if len(text) > 500:
            text = text[:500] + "..."

        console.print(Panel(
            f"[bold]{title}[/bold]\n\n"
            f"[dim]Date: {date}[/dim]\n"
            f"[dim]Source: {source}[/dim]\n\n"
            f"{text}",
            title="✅ Article Extracted",
            border_style="green"
        ))


def save_scraped_content(result: dict, url: str, save_dir: str = "data/scraped") -> Optional[str]:
    """
    Save scraped article content to a JSON file.

    Args:
        result: The scrape result dict
        url: The original URL
        save_dir: Directory to save to

    Returns:
        Path to saved file, or None if saving failed
    """
    try:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        domain = urlparse(url).netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{domain}.json"

        filepath = save_path / filename

        save_data = {
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": result.get("title"),
            "date": result.get("date"),
            "source": result.get("source"),
            "final_url": result.get("final_url"),
            "text": result.get("text"),
            "extraction_method": result.get("extraction_method"),
            "user_agent_used": result.get("user_agent_used"),
            "location_used": result.get("location_used"),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        return str(filepath)
    except Exception:
        return None


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL of the article to scrape"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    output: str = typer.Option("pretty", "--output", "-o", help="Output format: pretty, json"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save scraped content to data/scraped/"),
    save_dir: str = typer.Option("data/scraped", "--save-dir", help="Directory to save scraped content"),
    config: str = typer.Option(None, "--config", "-c", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Scrape an article from a URL.

    Examples:
        scraper scrape https://example.com/article
        scraper scrape https://bbc.com/news --no-headless
        scraper scrape https://example.com -o json
    """
    setup_logging(level="DEBUG" if verbose else "INFO")

    console.print(f"[bold blue]🚀 Scraping:[/bold blue] {url}")

    # Use default config path if not specified
    if config is None:
        config = f"{get_config_dir()}/config.json"

    try:
        scraper = WebScraper(config_path=config)
        result = scraper.extract_article(url, headless=headless)
        show_result(result, format=output)

        # Save scraped content if successful
        if "error" not in result and save:
            saved_path = save_scraped_content(result, url, save_dir=save_dir)
            if saved_path:
                console.print(f"[dim]💾 Content saved: {saved_path}[/dim]")

        if "error" in result:
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        raise typer.Exit(code=1) from None


@app.command()
def search(
    text: str = typer.Argument(..., help="Text snippet to search for"),
    results: int = typer.Option(3, "--results", "-n", help="Number of results to return"),
    output: str = typer.Option("pretty", "--output", "-o", help="Output format: pretty, json"),
):
    """
    Search for the original source of a text snippet.

    Examples:
        scraper search "Breaking news about technology"
        scraper search "Article text here" -n 5
    """
    setup_logging(level="INFO")

    console.print("[bold blue]🔍 Searching for source...[/bold blue]")

    try:
        scraper = WebScraper()
        search_results = scraper.find_source_from_text(text, num_results=results)

        if output == "json":
            console.print_json(data=search_results)
        else:
            if search_results and "error" not in search_results[0]:
                table = Table(title="Search Results")
                table.add_column("Title", style="cyan")
                table.add_column("URL", style="green")

                for res in search_results:
                    table.add_row(
                        res.get("title", "N/A")[:50],
                        res.get("url", "N/A")
                    )

                console.print(table)
            else:
                console.print("[yellow]No results found.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from None


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker processes"),
):
    """
    Start the API server.

    Examples:
        scraper serve
        scraper serve --port 8080
        scraper serve --reload
    """
    import uvicorn

    console.print(Panel(
        f"[bold green]Starting Web Scraper API[/bold green]\n\n"
        f"Host: {host}\n"
        f"Port: {port}\n"
        f"Workers: {workers}\n"
        f"Reload: {reload}\n\n"
        f"[dim]Press Ctrl+C to stop[/dim]",
        title="🌐 API Server",
        border_style="blue"
    ))

    uvicorn.run(
        "app.api.scraper_api:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
    )


@app.command()
def stats():
    """
    Show scraping statistics.
    """
    setup_logging(level="WARNING")

    try:
        scraper = WebScraper()
        stats = scraper.get_stats()

        table = Table(title="Scraping Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in stats.items():
            table.add_row(str(key).replace("_", " ").title(), str(value))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def version():
    """Show version information."""
    console.print(Panel(
        "[bold]Web Scraper[/bold]\n"
        "Version: 2.0.0\n\n"
        "[dim]Features:[/dim]\n"
        "• 50+ rotating user agents\n"
        "• 30+ location profiles\n"
        "• Anti-detection scripts\n"
        "• CAPTCHA solving\n"
        "• Proxy rotation\n"
        "• Human behavior simulation",
        title="ℹ️ About",
        border_style="blue"
    ))


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
