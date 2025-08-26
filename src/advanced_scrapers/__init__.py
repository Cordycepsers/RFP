"""
Advanced scrapers for hard-to-scrape websites using Playwright MCP integration.
These scrapers handle complex JavaScript, authentication, and dynamic content.
"""

__version__ = "1.0.0"
__author__ = "Proposaland Monitor"

from .base_advanced_scraper import BaseAdvancedScraper
from .devex_advanced import DevexAdvancedScraper

__all__ = [
    'BaseAdvancedScraper',
    'DevexAdvancedScraper'
]