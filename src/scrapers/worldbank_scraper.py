"""
World Bank Scraper
Scrapes procurement opportunities from World Bank Projects & Operations
https://projects.worldbank.org/en/projects-operations/procurement
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import re
import time

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from .base_scraper import OpportunityData, BaseScraper


class WorldBankScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        if website_config is None:
            website_config = {
                'name': 'World Bank',
                'url': 'https://projects.worldbank.org/en/projects-operations/procurement?srce=both',
                'type': 'worldbank',
                'priority': 1.0
            }
        super().__init__(config, website_config)
        self.name = 'World Bank'
        # JSON procurement API (public search.worldbank.org)
        self.api_url = 'https://search.worldbank.org/api/procurement'
        scraper_config = config.get('scraper_configs', {}).get('worldbank', {})
        self.max_pages = scraper_config.get('max_pages', 5)
        self.results_per_page = scraper_config.get('results_per_page', 20)
        self.max_opportunities = scraper_config.get('max_opportunities', 100)
        self.request_delay = scraper_config.get('request_delay', 1.5)
        self.logger = logging.getLogger(__name__)

    def scrape_opportunities(self) -> List[OpportunityData]:
        opportunities: List[OpportunityData] = []
        try:
            self.logger.info("Starting World Bank scraping via JSON API")
            start = 0
            for page in range(self.max_pages):
                params = {
                    'format': 'json',
                    'rows': self.results_per_page,
                    'start': start,
                    'apilang': 'en'
                }
                try:
                    data = None
                    # Retry up to 2 times on 5xx responses
                    for attempt in range(1, 3):
                        r = self.session.get(self.api_url, params=params, timeout=self.timeout)
                        if r.ok:
                            data = r.json()
                            break
                        # retry only on server errors
                        if 500 <= r.status_code < 600:
                            self.logger.warning(f"World Bank API {r.status_code}; retry {attempt}/2")
                            time.sleep(min(5.0, self.request_delay * attempt))
                            continue
                        else:
                            self.logger.warning(f"World Bank API returned {r.status_code}; stopping")
                            break
                    if data is None:
                        break
                except Timeout as te:
                    self.logger.error(f"Timeout error fetching World Bank data: {te}")
                    break
                except ConnectionError as ce:
                    self.logger.error(f"Connection error with World Bank API: {ce}")
                    break
                except HTTPError as he:
                    self.logger.error(f"HTTP error from World Bank API: {he}")
                    break
                except RequestException as re:
                    self.logger.error(f"Request error with World Bank API: {re}")
                    break
                except ValueError as ve:
                    self.logger.error(f"JSON parsing error for World Bank data: {ve}")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error fetching/parsing World Bank JSON: {e}")
                    raise e

                items = self._extract_items_from_api(data)
                if not items:
                    self.logger.info("No items returned; stopping pagination")
                    break

                for it in items:
                    opp = self._map_api_item_to_opportunity(it)
                    if opp and self.is_relevant_opportunity(opp):
                        opportunities.append(opp)
                        if len(opportunities) >= self.max_opportunities:
                            break
                if len(opportunities) >= self.max_opportunities:
                    break

                start += self.results_per_page
                if page < self.max_pages - 1:
                    time.sleep(self.request_delay)
        except RequestException as re:
            self.logger.error(f"Network error while scraping World Bank: {re}")
        except ValueError as ve:
            self.logger.error(f"Data processing error while scraping World Bank: {ve}")
        except Exception as e:
            self.logger.error(f"Unexpected error scraping World Bank: {e}")
            raise

        self.logger.info(f"World Bank scraping completed. Found {len(opportunities)} relevant opportunities")
        return opportunities

    def _extract_items_from_api(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            # Some WB APIs return dict keyed by numeric strings under 'proc' or 'projects'
            if isinstance(data, dict):
                for key in ['proc', 'records', 'results']:
                    if key in data and isinstance(data[key], dict):
                        return list(data[key].values())
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # Fallback: if top-level is dict of items
                if all(isinstance(v, dict) for v in data.values()):
                    return list(data.values())
        except (KeyError, TypeError, ValueError) as e:
            self.logger.debug(f"Error extracting World Bank API items: {e}")
        return []

    def _map_api_item_to_opportunity(self, it: Dict[str, Any]) -> Optional[OpportunityData]:
        try:
            title = it.get('procname') or it.get('title') or ''
            if not title:
                return None
            opp = OpportunityData()
            opp.title = title
            opp.description = it.get('procdetails') or title
            opp.organization = 'World Bank'
            opp.location = it.get('countryname') or it.get('country') or ''
            opp.reference_number = it.get('projectid') or it.get('project_id') or ''
            opp.reference_confidence = 0.7 if opp.reference_number else 0.0
            opp.source_url = it.get('url') or it.get('link') or ''
            # Published date
            pub = it.get('pubdate') or it.get('date')
            if pub:
                try:
                    opp.extracted_date = datetime.fromisoformat(pub)  # if iso
                except (ValueError, TypeError):
                    # Common WB formats
                    for fmt in ['%B %d, %Y', '%b %d, %Y', '%d-%b-%Y', '%Y-%m-%d']:
                        try:
                            opp.extracted_date = datetime.strptime(str(pub), fmt)
                            break
                        except (ValueError, TypeError):
                            continue
            # Keywords and budget
            opp.keywords_found = self.extract_keywords(f"{opp.title} {opp.description}")
            # No budget/deadline in API usually
            return opp
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            self.logger.warning(f"Data mapping error for World Bank item: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error mapping World Bank item: {e}")
            raise RuntimeError(f"Unexpected error mapping World Bank item: {e}. Data: {it}") from e
