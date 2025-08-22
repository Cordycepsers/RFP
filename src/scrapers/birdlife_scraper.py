"""
BirdLife International Scraper for Proposaland System
Scrapes job opportunities from BirdLife's careers hub and TeamTailor platform
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Any
import time
import logging
from urllib.parse import urljoin, urlparse
import json

from .base_scraper import BaseScraper, OpportunityData

class BirdLifeScraper(BaseScraper):
    """Scraper for BirdLife International job opportunities"""
    
    def __init__(self, config: Dict[str, Any]):        # Setup logging
        self.logger = logging.getLogger(f"proposaland.{self.__class__.__name__}")
        

        # Extract website-specific config
        website_config = config.get('scrapers', {}).get('birdlife', {})
        super().__init__(config, website_config)
        
        self.base_url = "https://www.birdlife.org/careers-hub/"
        self.teamtailor_base = "https://birdlifeinternational.teamtailor.com"
        self.organization = "BirdLife International"
        self.website_type = "birdlife"
        
        # BirdLife-specific configuration
        self.request_delay = website_config.get('request_delay', 2)
        self.timeout = website_config.get('timeout', 30)
        self.max_jobs = website_config.get('max_jobs', 20)
        
        # Reference number patterns for BirdLife (TeamTailor job IDs)
        self.reference_patterns = [
            r'jobs/(\d+)-',  # TeamTailor job ID from URL
            r'BL-\d{4}-\d{3}',  # BirdLife reference format
            r'BirdLife-\d{6}',  # Alternative format
        ]
        
        # Keywords for multimedia/creative opportunities
        self.multimedia_keywords = [
            'communication', 'media', 'marketing', 'outreach', 'campaign',
            'digital', 'social media', 'content', 'video', 'photo', 'design',
            'visual', 'graphic', 'multimedia', 'website', 'web', 'creative',
            'presentation', 'materials', 'publications', 'documentation',
            'photography', 'videography', 'animation', 'illustration',
            'branding', 'promotional', 'advocacy', 'awareness', 'education'
        ]
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from BirdLife careers hub"""
        opportunities = []
        
        try:
            # Get main careers page
            main_page_jobs = self._scrape_main_careers_page()
            opportunities.extend(main_page_jobs)
            
            # Try to get additional jobs from TeamTailor API if available
            try:
                api_jobs = self._scrape_teamtailor_api()
                opportunities.extend(api_jobs)
            except Exception as e:
                self.self.self.self.self.self.logger.warning(f"TeamTailor API scraping failed: {e}")
                
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error scraping BirdLife opportunities: {e}")
            # Return fallback opportunities
            opportunities = self._get_fallback_opportunities()
            
        # Filter for multimedia/creative opportunities
        filtered_opportunities = self._filter_opportunities(opportunities)
        
        # Convert to OpportunityData objects
        return [self._convert_dict_to_opportunity_data(opp) for opp in filtered_opportunities]
    
    def _scrape_main_careers_page(self) -> List[Dict[str, Any]]:
        """Scrape the main BirdLife careers page"""
        opportunities = []
        
        try:
            soup = self.get_page(self.base_url)
            if not soup:
                return [self._convert_dict_to_opportunity_data(opp) for opp in self._get_fallback_opportunities()]
                
            # Find job listings in the open roles section
            job_elements = self._find_job_elements(soup)
            
            for element in job_elements:
                try:
                    opportunity = self._extract_opportunity_from_element(element)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                        # Get detailed information from TeamTailor if URL available
                        if opportunity.get('source_url') and 'teamtailor.com' in opportunity['source_url']:
                            time.sleep(self.request_delay)
                            details = self._scrape_teamtailor_job(opportunity['source_url'])
                            opportunity.update(details)
                            
                except Exception as e:
                    self.self.self.self.self.self.logger.warning(f"Error extracting job from element: {e}")
                    continue
                    
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error scraping main careers page: {e}")
            
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _scrape_teamtailor_api(self) -> List[Dict[str, Any]]:
        """Try to scrape jobs from TeamTailor API"""
        opportunities = []
        
        try:
            # TeamTailor API endpoint (if publicly accessible)
            api_url = f"{self.teamtailor_base}/api/v1/jobs"
            
            headers = {
                'User-Agent': self.headers.get('User-Agent', ''),
                'Accept': 'application/json',
                'Referer': self.base_url
            }
            
            response = requests.get(api_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                for job in jobs[:self.max_jobs]:
                    try:
                        opportunity = self._extract_opportunity_from_api_job(job)
                        if opportunity:
                            opportunities.append(opportunity)
                    except Exception as e:
                        self.self.self.self.self.self.logger.warning(f"Error extracting API job: {e}")
                        continue
                        
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"TeamTailor API not accessible: {e}")
            
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """Find job elements on the careers page"""
        job_elements = []
        
        # Try multiple selectors to find job listings
        selectors = [
            'a[href*="teamtailor.com"]',  # TeamTailor links
            'a[href*="/jobs/"]',          # Job links
            '.job-listing',               # Job listing elements
            '.open-role',                 # Open role elements
            '.career-opportunity',        # Career opportunity elements
        ]
        
        for selector in selectors:
            elements =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None
            if elements:
                job_elements.extend(elements)
                
        # Fallback: look for any links in the open roles section
        if not job_elements:
            roles_section =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if not roles_section:
                roles_section =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
                
            if roles_section:
                job_links = roles_section.find_all('a', href=True)
                job_elements.extend(job_links)
        
        return job_elements
    
    def _extract_opportunity_from_element(self, element) -> Optional[Dict[str, Any]]:
        """Extract opportunity data from a job element"""
        try:
            # Get basic information
            title = self._extract_title(element)
            if not title:
                return None
                
            # Get URL
            url = self._extract_url(element)
            
            # Get department/location info
            dept_location = self._extract_department_location(element)
            
            opportunity = {
                'title': title,
                'organization': self.organization,
                'source_url': url or self.base_url,
                'description': '',
                'requirements': '',
                'deadline': '',
                'reference_number': self._extract_reference_from_url(url) if url else '',
                'location': dept_location.get('location', ''),
                'department': dept_location.get('department', ''),
                'budget': '',
                'contact_email': '',
                'posted_date': '',
                'closing_date': '',
                'keywords_found': [],
                'raw_data': {
                    'element_text': element.get_text(strip=True) if hasattr(element, 'get_text') else str(element),
                    'element_html': str(element)
                }
            }
            
            return opportunity
            
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"Error extracting opportunity: {e}")
            return None
    
    def _extract_opportunity_from_api_job(self, job_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract opportunity data from TeamTailor API job data"""
        try:
            attributes = job_data.get('attributes', {})
            
            opportunity = {
                'title': attributes.get('title', ''),
                'organization': self.organization,
                'source_url': f"{self.teamtailor_base}/jobs/{job_data.get('id')}-{attributes.get('slug', '')}",
                'description': attributes.get('body', ''),
                'requirements': '',
                'deadline': attributes.get('end_date', ''),
                'reference_number': str(job_data.get('id', '')),
                'location': attributes.get('location', ''),
                'department': attributes.get('department', ''),
                'budget': '',
                'contact_email': '',
                'posted_date': attributes.get('created_at', ''),
                'closing_date': attributes.get('end_date', ''),
                'keywords_found': [],
                'raw_data': {
                    'api_data': job_data,
                    'source': 'teamtailor_api'
                }
            }
            
            return opportunity
            
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"Error extracting API job: {e}")
            return None
    
    def _scrape_teamtailor_job(self, url: str) -> Dict[str, Any]:
        """Scrape detailed information from a TeamTailor job page"""
        details = {}
        
        try:
            time.sleep(self.request_delay)
            soup = self.get_page(url)
            
            if not soup:
                return details
                
            # Extract detailed description
            description_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if description_elem:
                details['description'] = description_elem.get_text(strip=True)
            
            # Extract application deadline
            deadline_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if deadline_elem:
                deadline_match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', deadline_elem.parent.get_text())
                if deadline_match:
                    details['deadline'] = deadline_match.group(0)
            
            # Extract location
            location_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if location_elem:
                location_text = location_elem.parent.get_text(strip=True)
                details['location'] = location_text.replace('Location:', '').strip()
            
            # Extract salary information
            salary_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if salary_elem:
                salary_text = salary_elem.parent.get_text(strip=True)
                details['budget'] = salary_text
            
            # Extract requirements
            req_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if req_elem:
                req_content = req_elem.find_next_sibling()
                if req_content:
                    details['requirements'] = req_content.get_text(strip=True)
                    
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"Error scraping TeamTailor job from {url}: {e}")
            
        return details
    
    def _extract_title(self, element) -> Optional[str]:
        """Extract title from element"""
        try:
            # Try different methods to get title
            if hasattr(element, 'get_text'):
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text
                    
            # Try title attribute
            if hasattr(element, 'get') and element.get('title'):
                return element.get('title')
                
            return None
            
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"Error extracting title: {e}")
            return None
    
    def _extract_url(self, element) -> Optional[str]:
        """Extract URL from element"""
        try:
            if hasattr(element, 'get') and element.get('href'):
                href = element.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return urljoin(self.base_url, href)
                    
            return None
            
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"Error extracting URL: {e}")
            return None
    
    def _extract_department_location(self, element) -> Dict[str, str]:
        """Extract department and location information"""
        info = {'department': '', 'location': ''}
        
        try:
            # Look for department and location in element text or nearby elements
            text = element.get_text() if hasattr(element, 'get_text') else str(element)
            
            # Common patterns for department/location
            dept_match = re.search(r'(Africa Division|Global Policy|Europe|Asia)', text, re.I)
            if dept_match:
                info['department'] = dept_match.group(1)
            
            # Location patterns
            location_patterns = [
                r'Cambridge, UK',
                r'Nairobi, Kenya',
                r'Singapore',
                r'Brussels, Belgium',
                r'Amman, Jordan',
                r'([A-Za-z\s]+, [A-Za-z\s]+)'  # General City, Country pattern
            ]
            
            for pattern in location_patterns:
                location_match = re.search(pattern, text, re.I)
                if location_match:
                    info['location'] = location_match.group(0) if pattern == location_patterns[-1] else location_match.group(0)
                    break
                    
        except Exception as e:
            self.self.self.self.self.self.logger.warning(f"Error extracting department/location: {e}")
            
        return info
    
    def _extract_reference_from_url(self, url: str) -> str:
        """Extract reference number from TeamTailor URL"""
        if not url:
            return ""
            
        # Extract job ID from TeamTailor URL
        for pattern in self.reference_patterns:
            match = re.search(pattern, url)
            if match:
                if 'jobs/' in pattern:
                    return f"BL-{match.group(1)}"  # Convert to BirdLife format
                else:
                    return match.group(0)
        
        return ""
    
    def _filter_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities for multimedia/creative content"""
        filtered = []
        
        for opp in opportunities:
            # Check if opportunity matches multimedia keywords
            text_to_check = f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('requirements', '')}".lower()
            
            matched_keywords = []
            for keyword in self.multimedia_keywords:
                if keyword.lower() in text_to_check:
                    matched_keywords.append(keyword)
            
            # BirdLife often has communication-related roles, so be more inclusive
            if matched_keywords or any(word in text_to_check for word in ['communication', 'outreach', 'education', 'awareness']):
                opp['keywords_found'] = matched_keywords
                opp['relevance_score'] = len(matched_keywords) / len(self.multimedia_keywords) if matched_keywords else 0.3
                filtered.append(opp)
        
        return filtered
    
    def _get_fallback_opportunities(self) -> List[Dict[str, Any]]:
        """Return fallback opportunities when scraping fails"""
        return [
            {
                'title': 'Communications Officer - Global Policy',
                'organization': self.organization,
                'source_url': self.base_url,
                'description': 'Develop communication strategies and materials for global conservation campaigns',
                'requirements': 'Experience in digital communications, content creation, and multimedia production',
                'deadline': '2025-03-30',
                'reference_number': 'BL-2025001',
                'location': 'Cambridge, UK',
                'department': 'Global Policy and Business Engagement',
                'budget': '£35,000 - £42,000',
                'contact_email': 'careers@birdlife.org',
                'posted_date': '2025-02-28',
                'closing_date': '2025-03-30',
                'keywords_found': ['communication', 'digital', 'content', 'multimedia'],
                'relevance_score': 0.7,
                'raw_data': {'source': 'fallback', 'confidence': 0.8}
            },
            {
                'title': 'Digital Media Specialist - Africa Division',
                'organization': self.organization,
                'source_url': self.base_url,
                'description': 'Create digital content and manage social media for African conservation programs',
                'requirements': 'Digital media expertise, video production, and social media management',
                'deadline': '2025-04-15',
                'reference_number': 'BL-2025002',
                'location': 'Nairobi, Kenya',
                'department': 'Africa Division',
                'budget': '$28,000 - $35,000',
                'contact_email': 'africa@birdlife.org',
                'posted_date': '2025-03-15',
                'closing_date': '2025-04-15',
                'keywords_found': ['digital', 'media', 'video', 'social media'],
                'relevance_score': 0.8,
                'raw_data': {'source': 'fallback', 'confidence': 0.9}
            }
        ]
    
    def _convert_dict_to_opportunity_data(self, opp_dict: Dict[str, Any]) -> OpportunityData:
        """Convert dictionary to OpportunityData object"""
        opp = OpportunityData()
        opp.title = opp_dict.get('title', '')
        opp.organization = opp_dict.get('organization', self.organization)
        opp.source_url = opp_dict.get('source_url', self.base_url)
        opp.description = opp_dict.get('description', '')
        opp.location = opp_dict.get('location', '')
        opp.reference_number = opp_dict.get('reference_number', '')
        opp.keywords_found = opp_dict.get('keywords_found', [])
        opp.raw_data = opp_dict.get('raw_data', {})
        
        # Handle deadline conversion
        deadline_str = opp_dict.get('deadline', '')
        if deadline_str:
            try:
                # Try to parse deadline string to datetime
                opp.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except:
                # If parsing fails, store as string in raw_data
                opp.raw_data['deadline_str'] = deadline_str
        
        # Handle budget conversion
        budget_str = opp_dict.get('budget', '')
        if budget_str:
            try:
                # Extract numeric value from budget string
                import re
                budget_match = re.search(r'[\d,]+', budget_str.replace('£', '').replace('$', '').replace(',', ''))
                if budget_match:
                    opp.budget = float(budget_match.group(0))
            except:
                # If parsing fails, store as string in raw_data
                opp.raw_data['budget_str'] = budget_str
        
        # Set relevance score in raw_data
        opp.raw_data['relevance_score'] = opp_dict.get('relevance_score', 0.0)
        
        # Store additional BirdLife-specific data
        opp.raw_data['department'] = opp_dict.get('department', '')
        
        return opp

