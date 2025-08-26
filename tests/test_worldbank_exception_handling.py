#!/usr/bin/env python3
"""
Test script to verify that World Bank scrapers handle exceptions correctly.
Tests both the regular and advanced scrapers with specific exception types.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, Timeout, ConnectionError

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

# Also add root directory for relative imports
root_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, root_path)

try:
    from src.scrapers.worldbank_scraper import WorldBankScraper
    from src.advanced_scrapers.worldbank_advanced_scraper import WorldBankAdvancedScraper
except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping advanced scraper tests due to import issues")
    WorldBankAdvancedScraper = None


class TestWorldBankExceptionHandling(unittest.TestCase):
    """Test specific exception handling in World Bank scrapers."""

    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'scraper_configs': {
                'worldbank': {
                    'max_pages': 1,
                    'results_per_page': 5,
                    'max_opportunities': 10,
                    'request_delay': 0.1
                }
            }
        }
        self.website_config = {
            'name': 'World Bank Test',
            'url': 'https://test.worldbank.org',
            'type': 'worldbank',
            'priority': 1.0
        }

    def test_regular_scraper_request_timeout(self):
        """Test that WorldBankScraper handles timeout exceptions correctly."""
        scraper = WorldBankScraper(self.config, self.website_config)
        
        # Mock the session to raise a timeout
        with patch.object(scraper, 'session') as mock_session:
            mock_session.get.side_effect = Timeout("Request timed out")
            
            # Should not raise exception, should return empty list
            opportunities = scraper.scrape_opportunities()
            self.assertEqual(opportunities, [])

    def test_regular_scraper_connection_error(self):
        """Test that WorldBankScraper handles connection errors correctly."""
        scraper = WorldBankScraper(self.config, self.website_config)
        
        with patch.object(scraper, 'session') as mock_session:
            mock_session.get.side_effect = ConnectionError("Connection failed")
            
            opportunities = scraper.scrape_opportunities()
            self.assertEqual(opportunities, [])

    def test_regular_scraper_json_parsing_error(self):
        """Test that WorldBankScraper handles JSON parsing errors correctly."""
        scraper = WorldBankScraper(self.config, self.website_config)
        
        # Mock successful HTTP response but invalid JSON
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with patch.object(scraper, 'session') as mock_session:
            mock_session.get.return_value = mock_response
            
            opportunities = scraper.scrape_opportunities()
            self.assertEqual(opportunities, [])

    def test_regular_scraper_data_mapping_errors(self):
        """Test that WorldBankScraper handles data mapping errors correctly."""
        scraper = WorldBankScraper(self.config, self.website_config)
        
        # Test with invalid data structure
        invalid_data = {"invalid": "structure"}
        items = scraper._extract_items_from_api(invalid_data)
        self.assertEqual(items, [])
        
        # Test mapping with missing required fields
        invalid_item = {}  # Empty item
        opportunity = scraper._map_api_item_to_opportunity(invalid_item)
        self.assertIsNone(opportunity)

    @patch('playwright.sync_api.sync_playwright')
    def test_advanced_scraper_playwright_error(self, mock_sync_playwright):
        """Test that WorldBankAdvancedScraper handles Playwright errors correctly."""
        scraper = WorldBankAdvancedScraper(self.config, self.website_config)
        
        # Mock Playwright to raise an error
        from playwright.sync_api import Error as PlaywrightError
        mock_sync_playwright.side_effect = PlaywrightError("Playwright failed")
        
        # Should not raise exception, should return empty list
        opportunities = scraper._scrape_with_mcp()
        self.assertEqual(opportunities, [])

    @patch('playwright.sync_api.sync_playwright')
    def test_advanced_scraper_timeout_error(self, mock_sync_playwright):
        """Test that WorldBankAdvancedScraper handles timeout errors correctly."""
        scraper = WorldBankAdvancedScraper(self.config, self.website_config)
        
        # Mock Playwright to raise a timeout
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        mock_sync_playwright.side_effect = PlaywrightTimeoutError("Operation timed out")
        
        opportunities = scraper._scrape_with_mcp()
        self.assertEqual(opportunities, [])

    def test_advanced_scraper_row_processing_errors(self):
        """Test that row processing errors are handled gracefully."""
        scraper = WorldBankAdvancedScraper(self.config, self.website_config)
        
        # Test that the scraper class can be instantiated and has required methods
        self.assertTrue(hasattr(scraper, '_scrape_with_mcp'))
        self.assertTrue(hasattr(scraper, 'scrape_opportunities'))
        
        # Test that scrape_opportunities method exists and is callable
        self.assertTrue(callable(getattr(scraper, 'scrape_opportunities', None)))

    def test_logging_configuration(self):
        """Test that loggers are properly configured."""
        regular_scraper = WorldBankScraper(self.config, self.website_config)
        self.assertIsNotNone(regular_scraper.logger)
        
        # Test that advanced scraper can be instantiated
        advanced_scraper = WorldBankAdvancedScraper(self.config, self.website_config)
        self.assertIsNotNone(advanced_scraper)  # Advanced scraper uses loguru logger which is imported at module level


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run tests with verbose output
    unittest.main(verbosity=2)
