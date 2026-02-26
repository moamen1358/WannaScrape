"""
Content extraction logic using Trafilatura and fallback methods.
"""

import json
import logging
import trafilatura
from typing import Optional, Dict, Any
from playwright.sync_api import Page

logger = logging.getLogger("scraper.extractor")


class ContentExtractor:
    """
    Extracts article content from web pages using multiple strategies.
    """

    # Priority list of content container selectors
    CONTENT_SELECTORS = [
        "article",
        "[role='main']",
        "main",
        ".post-content",
        ".article-body",
        ".entry-content",
        "#main-content",
        ".page-content",
        ".article-content",
        ".blog-content",
        ".single-content",
        "[data-content]",
        ".wrapper .content",
        ".content",
        "#content",
        "#app main",
        "#__next main",
        "body"  # Last resort
    ]

    def extract_from_html(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract article content from HTML using Trafilatura.

        Args:
            html: Raw HTML content

        Returns:
            Parsed article data or None if extraction failed
        """
        try:
            result = trafilatura.extract(
                html,
                output_format="json",
                with_metadata=True,
                include_comments=False,
                favor_recall=True,
                include_tables=True,
                deduplicate=True
            )

            if result:
                return json.loads(result)

            return None
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")
            return None

    def extract_fallback(self, page: Page) -> str:
        """
        Fallback text extraction from specific content containers.

        Args:
            page: Playwright page object

        Returns:
            Extracted text or empty string
        """
        try:
            for selector in self.CONTENT_SELECTORS:
                loc = page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible():
                    text = loc.first.inner_text()
                    if len(text) > 500:
                        logger.info(f"Fallback extraction using: '{selector}'")
                        return text
        except Exception as e:
            logger.warning(f"Fallback extraction error: {e}")

        return ""

    def validate_content(self, text: str) -> Dict[str, Any]:
        """
        Validate extracted content for CAPTCHA phrases and minimum length.

        Args:
            text: Extracted text content

        Returns:
            Dict with 'valid' boolean and 'reason' if invalid
        """
        from app.config.constants import CAPTCHA_PHRASES

        text_lower = text.lower()

        # Check for CAPTCHA phrases
        for phrase in CAPTCHA_PHRASES:
            if phrase in text_lower:
                return {
                    "valid": False,
                    "reason": "captcha_detected",
                    "message": "CAPTCHA or bot detection blocked content extraction."
                }

        # Check minimum length
        if len(text) < 300:
            return {
                "valid": False,
                "reason": "insufficient_content",
                "message": "Insufficient content extracted. The page may be an error page, paywall, or require login."
            }

        return {"valid": True}

    def extract(self, page: Page) -> Dict[str, Any]:
        """
        Main extraction method that tries Trafilatura first, then fallback.

        Args:
            page: Playwright page object

        Returns:
            Extraction result with content or error information
        """
        html_content = page.content()
        final_url = page.url

        trafilatura_error = None

        # Try Trafilatura first
        result = self.extract_from_html(html_content)

        if result:
            text = result.get('text', '')
            validation = self.validate_content(text)

            if validation["valid"]:
                result['final_url'] = final_url
                result['extraction_method'] = 'trafilatura'
                return {
                    "success": True,
                    "data": result,
                    "method": "trafilatura"
                }

            # Trafilatura returned content but it failed validation.
            # If it's a CAPTCHA detection, return immediately — fallback won't help.
            if validation["reason"] == "captcha_detected":
                return {
                    "success": False,
                    "error": validation["message"],
                    "error_type": validation["reason"],
                    "extracted_text": text[:500] if text else None,
                    "final_url": final_url,
                    "method": "trafilatura"
                }

            # For insufficient content, fall through to fallback extraction.
            # JS-heavy pages often have content in the DOM that Trafilatura misses.
            logger.info(
                f"Trafilatura extracted only {len(text)} chars (min 300). "
                f"Trying fallback extraction..."
            )
            trafilatura_error = {
                "error": validation["message"],
                "error_type": validation["reason"],
                "extracted_text": text[:500] if text else None,
            }

        # Try fallback extraction (also used when Trafilatura content is insufficient)
        fallback_text = self.extract_fallback(page)

        if fallback_text and len(fallback_text) > 500:
            validation = self.validate_content(fallback_text)

            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["message"],
                    "error_type": validation["reason"],
                    "extracted_text": fallback_text[:500],
                    "final_url": final_url,
                    "method": "fallback"
                }

            # Get the page title from the browser instead of hardcoding
            try:
                page_title = page.title() or "Extracted Content (Fallback)"
                # Clean up title — remove trailing " - SiteName" patterns if too long
                if len(page_title) > 200:
                    page_title = page_title[:200]
            except Exception:
                page_title = "Extracted Content (Fallback)"

            logger.warning("Trafilatura failed. Using fallback extraction.")
            return {
                "success": True,
                "data": {
                    "title": page_title,
                    "date": None,
                    "source": final_url,
                    "text": fallback_text,
                    "final_url": final_url,
                },
                "method": "fallback"
            }

        # No content extracted — return the Trafilatura error if we had one,
        # otherwise return a generic no-content error.
        if trafilatura_error:
            return {
                "success": False,
                "error": trafilatura_error["error"],
                "error_type": trafilatura_error["error_type"],
                "extracted_text": trafilatura_error["extracted_text"],
                "final_url": final_url,
                "method": "trafilatura"
            }

        return {
            "success": False,
            "error": "Could not extract content from the page.",
            "error_type": "no_content",
            "final_url": final_url,
            "method": "none"
        }


def check_expired_link(content: str) -> bool:
    """Check if the page indicates an expired Google News link."""
    content_lower = content.lower()
    return "this feed is not available" in content_lower or "news:unfepa" in content_lower
