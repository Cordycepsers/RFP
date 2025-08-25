#!/usr/bin/env python3
"""
Enhanced Devex Video Opportunities Scraper with Login and Detailed Extraction
Logs in with credentials, clicks each project, and extracts detailed descriptions
"""

import time
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import gspread
from google.oauth2.service_account import Credentials


class DevexEnhancedScraper:
    """Enhanced Selenium scraper for Devex with login and detailed extraction"""

    def __init__(self, email: str, password: str, google_credentials_path: str = None):
        self.email = email
        self.password = password
        self.base_url = "https://www.devex.com"
        self.login_url = "https://www.devex.com/login"
        self.video_search_url = "https://www.devex.com/funding/r?report=tender-812898&query%5B%5D=video&filter%5Btype%5D%5B%5D=grant&filter%5Btype%5D%5B%5D=tender&filter%5Bstatuses%5D%5B%5D=forecast&filter%5Bstatuses%5D%5B%5D=open&filter%5Bupdated_since%5D=2025-08-17T17%3A57%3A37.879Z&sorting%5Border%5D=desc&sorting%5Bfield%5D=updated_at"

        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option(
            'useAutomationExtension', False)
        # Comment out for debugging - uncomment for production
        # self.chrome_options.add_argument("--headless")

        self.driver = None
        self.wait = None

        # Google Sheets setup
        self.google_credentials_path = google_credentials_path
        self.gc = None
        self.sheet = None

        # Data storage
        self.scraped_opportunities = []
        self.logged_in = False

    def setup_driver(self):
        """Initialize the Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            print("✓ Chrome driver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            return False

    def login(self):
        """Login to Devex with provided credentials by navigating to funding page first"""
        try:
            print("🔐 Logging in to Devex...")
            print("📄 Navigating to funding page to avoid OAuth redirect...")
            print(f"📧 Using email: {self.email}")
            print(f"🔑 Using password: {'*' * len(self.password)}")

            # Navigate to the funding search page first (avoids OAuth redirect)
            self.driver.get(self.video_search_url)
            time.sleep(5)

            # Debug: Print page information
            print(f"Debug: Current URL: {self.driver.current_url}")
            print(f"Debug: Page title: {self.driver.title}")

            # Handle any popups first
            self._handle_popups()

            # Look for Sign In button at the end of the page
            print("🔍 Looking for Sign In button at the end of the page...")

            # Scroll to bottom to make sure Sign In button is visible
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Look for Sign In link/button
            signin_selectors = [
                'a[href*="login"]',
                'a:contains("Sign In")',
                'a:contains("Sign in")',
                'a:contains("Login")',
                '.signin-link',
                '.login-link'
            ]

            signin_link = None
            for selector in signin_selectors:
                try:
                    if ':contains(' in selector:
                        signin_link = self.driver.find_element(
                            By.XPATH, f"//a[contains(text(), 'Sign In') or contains(text(), 'Sign in') or contains(text(), 'Login')]")
                    else:
                        signin_link = self.driver.find_element(
                            By.CSS_SELECTOR, selector)
                    print(f"✓ Found Sign In link with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not signin_link:
                print("❌ Could not find Sign In link on funding page")
                return False

            # Click the Sign In link
            signin_link.click()
            print("✓ Clicked Sign In link")
            time.sleep(5)

            # Now we should be on the login page - continue with form filling
            print("📝 Now filling in login form...")

            # Wait for login form to be visible
            self.wait.until(EC.presence_of_element_located(
                (By.TAG_NAME, "form")))

            # Debug: Find all input fields
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"Debug: Found {len(all_inputs)} input fields")
            for i, inp in enumerate(all_inputs):
                print(f"  Input {i}: type='{inp.get_attribute('type')}', name='{inp.get_attribute('name')}', id='{inp.get_attribute('id')}', placeholder='{inp.get_attribute('placeholder')}', class='{inp.get_attribute('class')}'")

            # Debug: Find all buttons
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"Debug: Found {len(all_buttons)} buttons")
            for i, btn in enumerate(all_buttons):
                print(
                    f"  Button {i}: type='{btn.get_attribute('type')}', text='{btn.text}', class='{btn.get_attribute('class')}'")

            # Find and fill email field
            email_selectors = [
                'input[name="email"]',
                'input[type="email"]',
                'input[id*="email"]',
                'input[placeholder*="email" i]',
                'input[name="username"]',
                'input[id*="username"]',
                'input[placeholder*="Email" i]'
            ]

            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    print(f"✓ Found email field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not email_field:
                print("❌ Could not find email field. Trying first text input...")
                try:
                    email_field = self.driver.find_element(
                        By.CSS_SELECTOR, 'input[type="text"], input[type="email"]')
                    print("✓ Using first text/email input as email field")
                except NoSuchElementException:
                    print("❌ No email field found at all")
                    return False

            # Clear and enter email
            email_field.clear()
            time.sleep(1)
            email_field.send_keys(self.email)
            print(f"✓ Email entered: {self.email}")
            time.sleep(3)

            # Check if page redirected after entering email
            current_url_after_email = self.driver.current_url
            print(
                f"Debug: URL after entering email: {current_url_after_email}")

            if 'google' in current_url_after_email.lower() or 'gmail' in current_url_after_email.lower():
                print("⚠️ Redirected to Google/Gmail login. This might be OAuth flow.")
                print("⚠️ The email might be associated with Google SSO.")
                # For now, let's see if we can continue with Google login
                # You might need to handle Google OAuth here
                return False

            if current_url_after_email != self.driver.current_url:
                print(
                    "⚠️ Page changed after entering email. Checking for password field...")

            # Find and fill password field
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id*="password"]'
            ]

            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    print(f"✓ Found password field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not password_field:
                print("❌ Could not find password field after entering email")
                print("🔍 This might indicate:")
                print("   - Two-step login process")
                print("   - OAuth redirect to Google/Gmail")
                print("   - Email validation step")
                print("   - Page still loading")

                # Wait a bit more and try again
                print("⏳ Waiting longer for password field to appear...")
                time.sleep(5)

                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(
                            By.CSS_SELECTOR, selector)
                        print(
                            f"✓ Found password field after waiting: {selector}")
                        break
                    except NoSuchElementException:
                        continue

                if not password_field:
                    print(
                        "❌ Still no password field found. Check if manual intervention needed.")
                    return False

            # Clear and enter password
            password_field.clear()
            time.sleep(1)
            password_field.send_keys(self.password)
            print("✓ Password entered")
            time.sleep(2)

            # Find and click signin button (avoiding OAuth buttons)
            login_button = None

            # First try to find the main login form submit button (NOT OAuth buttons)
            try:
                # Look for submit button that's NOT an OAuth button
                all_submit_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                print(f"Debug: Found {len(all_submit_buttons)} submit buttons")

                for i, btn in enumerate(all_submit_buttons):
                    btn_text = btn.text.lower() if btn.text else ""
                    btn_class = btn.get_attribute('class') or ""
                    print(
                        f"  Submit button {i}: text='{btn.text}', class='{btn_class}'")

                    # Skip OAuth buttons
                    if any(oauth in btn_text for oauth in ['google', 'microsoft', 'linkedin', 'facebook', 'twitter']):
                        print(f"    ⚠️ Skipping OAuth button: {btn.text}")
                        continue

                    # Look for the main login button (input submit or button without OAuth text)
                    if btn.tag_name == 'input' or (btn.tag_name == 'button' and not btn_text):
                        login_button = btn
                        print(
                            f"    ✓ Selected main login button: {btn.text or 'input submit button'}")
                        break

            except Exception as e:
                print(f"Debug: Error finding submit buttons: {e}")

            # If no suitable button found, try specific selectors for non-OAuth buttons
            if not login_button:
                # Try to find input submit button specifically (usually the main form button)
                try:
                    login_button = self.driver.find_element(
                        By.CSS_SELECTOR, 'input[type="submit"]')
                    print("✓ Found input submit button (avoiding OAuth)")
                except NoSuchElementException:
                    pass

            # Try form-specific selectors
            if not login_button:
                form_selectors = [
                    'form input[type="submit"]',
                    'form button[type="submit"]:not(:contains("Google")):not(:contains("Microsoft"))',
                    '.btn-primary'
                ]

                for selector in form_selectors:
                    try:
                        if ':contains(' not in selector:
                            login_button = self.driver.find_element(
                                By.CSS_SELECTOR, selector)
                            print(
                                f"✓ Found signin button with CSS selector: {selector}")
                            break
                    except NoSuchElementException:
                        continue

            # Last resort: XPath to find submit button not containing OAuth text
            if not login_button:
                xpath_selectors = [
                    "//input[@type='submit']",
                    "//form//button[@type='submit'][not(contains(text(), 'Google')) and not(contains(text(), 'Microsoft')) and not(contains(text(), 'LinkedIn')) and not(contains(text(), 'Facebook'))]",
                    # Avoid "Sign in with" buttons
                    "//button[@type='submit'][not(contains(text(), 'with'))]"
                ]

                for xpath in xpath_selectors:
                    try:
                        login_button = self.driver.find_element(
                            By.XPATH, xpath)
                        print(f"✓ Found signin button with XPath: {xpath}")
                        break
                    except NoSuchElementException:
                        continue

            if login_button:
                try:
                    # Scroll to button and make sure it's visible
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", login_button)
                    time.sleep(1)

                    # Try regular click first
                    login_button.click()
                    print("✓ Login button clicked")
                except ElementClickInterceptedException:
                    print("⚠️ Element click intercepted, trying JavaScript click...")
                    self.driver.execute_script(
                        "arguments[0].click();", login_button)
                    print("✓ Login button clicked via JavaScript")
                except Exception as e:
                    if "not interactable" in str(e):
                        print(
                            "⚠️ Button not interactable, trying JavaScript click...")
                        self.driver.execute_script(
                            "arguments[0].click();", login_button)
                        print("✓ Login button clicked via JavaScript")
                    else:
                        print(f"⚠️ Error clicking button: {e}")
                        print("⚠️ Trying Enter key as fallback...")
                        password_field.send_keys(Keys.RETURN)
                        print("✓ Pressed Enter to login")
            else:
                # Try pressing Enter on password field as fallback
                print("⚠️ Login button not found, trying Enter key...")
                password_field.send_keys(Keys.RETURN)
                print("✓ Pressed Enter to login")

            # Wait for login to complete
            print("⏳ Waiting for login to complete...")
            time.sleep(8)

            # Check if login was successful
            current_url = self.driver.current_url
            print(f"Debug: URL after login attempt: {current_url}")

            if 'login' not in current_url.lower() or 'dashboard' in current_url.lower() or 'profile' in current_url.lower():
                self.logged_in = True
                print("✅ Successfully logged in to Devex")
                return True
            else:
                print("❌ Login may have failed - still on login page")
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, '.error, .alert, .message, [class*="error"]')
                    for error in error_elements:
                        if error.text.strip():
                            print(f"❌ Error message: {error.text}")
                except:
                    pass
                return False

        except Exception as e:
            print(f"❌ Error during login: {e}")
            import traceback
            traceback.print_exc()
            return False

    def setup_google_sheets(self, spreadsheet_id: str = "1hCmLJ3h7RJdofji77YGyBqPnnq0vMmvvGYyHMyE7R5M"):
        """Setup Google Sheets connection with enhanced headers"""
        try:
            if not self.google_credentials_path:
                print("⚠️ No Google credentials provided. Will save to JSON instead.")
                return False

            # Define the scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]

            # Load credentials
            creds = Credentials.from_service_account_file(
                self.google_credentials_path,
                scopes=scope
            )

            # Initialize gspread client
            self.gc = gspread.authorize(creds)

            # Open spreadsheet by ID
            try:
                spreadsheet = self.gc.open_by_key(spreadsheet_id)
                self.sheet = spreadsheet.sheet1
                print(f"✓ Connected to spreadsheet with ID: {spreadsheet_id}")
                print(f"✓ Spreadsheet title: {spreadsheet.title}")
            except Exception as e:
                print(
                    f"❌ Failed to open spreadsheet with ID {spreadsheet_id}: {e}")
                return False

            # Setup enhanced headers for detailed data
            headers = [
                'Title', 'Official Title', 'Type', 'Status', 'Updated',
                'Funded By', 'Tendering Organization', 'Location', 'Opportunity Size',
                'Deadline', 'Categories', 'Topics', 'Reference Number',
                'Background', 'Objective', 'Scope of Work', 'Qualification Requirements',
                'Documents Required', 'Performance Evaluation', 'Payment Terms',
                'Submission Instructions', 'Additional Information', 'URL', 'Scraped At'
            ]

            # Check if headers exist, if not add them
            try:
                existing_headers = self.sheet.row_values(1)
                if not existing_headers or len(existing_headers) < len(headers):
                    self.sheet.clear()
                    self.sheet.insert_row(headers, 1)
                    print("✓ Enhanced headers added to spreadsheet")
            except:
                self.sheet.insert_row(headers, 1)
                print("✓ Enhanced headers added to spreadsheet")

            return True

        except Exception as e:
            print(f"❌ Failed to setup Google Sheets: {e}")
            return False

    def navigate_to_search(self):
        """Navigate to the Devex video search page"""
        try:
            print("🔍 Navigating to Devex video search...")
            self.driver.get(self.video_search_url)
            time.sleep(5)

            # Handle any popups
            self._handle_popups()

            # Wait for search results to load
            try:
                self.wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[class*='funding'], [class*='tender'], [class*='grant'], .result"))
                )
                print("✓ Successfully navigated to search page")
                return True
            except TimeoutException:
                print("⚠️ Timeout waiting for search results. Continuing anyway...")
                return True

        except Exception as e:
            print(f"❌ Failed to navigate to search page: {e}")
            return False

    def _handle_popups(self):
        """Handle any popups or alert messages"""
        try:
            # Close session alert if present
            close_selectors = [
                "button[aria-label*='Close']",
                ".close",
                ".modal-close",
                "[data-dismiss='modal']"
            ]

            for selector in close_selectors:
                try:
                    close_button = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    if close_button.is_displayed():
                        close_button.click()
                        time.sleep(2)
                        print("✓ Closed popup")
                        break
                except NoSuchElementException:
                    continue
        except Exception as e:
            pass

        try:
            # Accept cookies if present
            cookie_selectors = [
                "button:contains('Accept')",
                "button:contains('OK')",
                ".cookie-accept",
                "[data-accept-cookies]"
            ]

            for selector in cookie_selectors:
                try:
                    if ':contains(' in selector:
                        cookie_button = self.driver.find_element(
                            By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'OK')]")
                    else:
                        cookie_button = self.driver.find_element(
                            By.CSS_SELECTOR, selector)

                    if cookie_button.is_displayed():
                        cookie_button.click()
                        time.sleep(2)
                        print("✓ Accepted cookies")
                        break
                except NoSuchElementException:
                    continue
        except Exception as e:
            pass

    def scrape_opportunities_detailed(self, max_opportunities: int = 10):
        """Scrape opportunities with detailed information by clicking each one"""
        try:
            print(
                f"📋 Starting detailed scraping (max {max_opportunities} opportunities)...")

            opportunities_processed = 0

            while opportunities_processed < max_opportunities:
                # Get opportunity links on current page
                opportunity_links = self._get_opportunity_links()

                if not opportunity_links:
                    print("⚠️ No opportunity links found on current page")
                    break

                print(
                    f"📄 Found {len(opportunity_links)} opportunities on current page")

                # Process each opportunity
                for i, link_element in enumerate(opportunity_links):
                    if opportunities_processed >= max_opportunities:
                        break

                    try:
                        print(
                            f"🔍 Processing opportunity {opportunities_processed + 1}/{max_opportunities}")

                        # Get the URL before clicking (in case element becomes stale)
                        opportunity_url = link_element.get_attribute('href')

                        # Click on the opportunity
                        self.driver.execute_script(
                            "arguments[0].click();", link_element)
                        time.sleep(3)

                        # Extract detailed information
                        detailed_opportunity = self._extract_detailed_opportunity(
                            opportunity_url)

                        if detailed_opportunity:
                            self.scraped_opportunities.append(
                                detailed_opportunity)
                            print(
                                f"✓ Extracted detailed info for: {detailed_opportunity.get('title', 'Unknown')[:50]}...")

                        opportunities_processed += 1

                        # Go back to search results
                        self.driver.back()
                        time.sleep(2)

                        # Re-find opportunity links (DOM may have changed)
                        opportunity_links = self._get_opportunity_links()

                    except Exception as e:
                        print(f"⚠️ Error processing opportunity {i}: {e}")
                        # Try to go back to search results
                        try:
                            self.driver.back()
                            time.sleep(2)
                        except:
                            pass
                        continue

                # Try to go to next page if we haven't reached the limit
                if opportunities_processed < max_opportunities:
                    if not self._go_to_next_page():
                        print("📄 No more pages available")
                        break
                    time.sleep(3)

            print(
                f"✅ Detailed scraping completed! Processed {len(self.scraped_opportunities)} opportunities")
            return True

        except Exception as e:
            print(f"❌ Error during detailed scraping: {e}")
            return False

    def _get_opportunity_links(self) -> List:
        """Get all opportunity links on the current page"""
        try:
            # Multiple selectors to find opportunity links
            link_selectors = [
                'a[href*="/funding/"]',
                'a[href*="/tender"]',
                'a[href*="/grant"]',
                '.funding-item a',
                '.tender-item a',
                '.grant-item a',
                '.opportunity-link',
                '.result-title a'
            ]

            all_links = []

            for selector in link_selectors:
                try:
                    links = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and ('/funding/' in href or '/tender' in href or '/grant' in href):
                            if link not in all_links:
                                all_links.append(link)
                except NoSuchElementException:
                    continue

            # Remove duplicates based on href
            unique_links = []
            seen_hrefs = set()

            for link in all_links:
                href = link.get_attribute('href')
                if href not in seen_hrefs:
                    unique_links.append(link)
                    seen_hrefs.add(href)

            # Limit to 10 per page to avoid overwhelming
            return unique_links[:10]

        except Exception as e:
            print(f"⚠️ Error getting opportunity links: {e}")
            return []

    def _extract_detailed_opportunity(self, opportunity_url: str) -> Optional[Dict]:
        """Extract detailed information from an opportunity page"""
        try:
            # Wait for page to load
            time.sleep(3)

            opportunity = {
                'title': '',
                'official_title': '',
                'type': '',
                'status': '',
                'updated': '',
                'funded_by': '',
                'tendering_organization': '',
                'location': '',
                'opportunity_size': '',
                'deadline': '',
                'categories': '',
                'topics': '',
                'reference_number': '',
                'background': '',
                'objective': '',
                'scope_of_work': '',
                'qualification_requirements': '',
                'documents_required': '',
                'performance_evaluation': '',
                'payment_terms': '',
                'submission_instructions': '',
                'additional_information': '',
                'url': opportunity_url,
                'scraped_at': datetime.now().isoformat()
            }

            # Extract title
            title_selectors = [
                'h1',
                '.opportunity-title',
                '.tender-title',
                '.grant-title',
                '[class*="title"]'
            ]

            for selector in title_selectors:
                try:
                    title_elem = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    opportunity['title'] = title_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue

            # Extract key information section
            self._extract_key_information(opportunity)

            # Extract detailed sections
            self._extract_detailed_sections(opportunity)

            # Extract all text content as additional information
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                # Clean and limit the text
                clean_text = re.sub(r'\s+', ' ', body_text).strip()
                opportunity['additional_information'] = clean_text[:2000] + \
                    "..." if len(clean_text) > 2000 else clean_text
            except:
                pass

            return opportunity if opportunity['title'] else None

        except Exception as e:
            print(f"⚠️ Error extracting detailed opportunity: {e}")
            return None

    def _extract_key_information(self, opportunity: Dict):
        """Extract key information fields"""
        try:
            # Look for key-value pairs in the page
            key_value_patterns = [
                (r'Funded by[:\s]*([^\\n]+)', 'funded_by'),
                (r'Location[:\s]*([^\\n]+)', 'location'),
                (r'Status[:\s]*([^\\n]+)', 'status'),
                (r'Tendering Organization[:\s]*([^\\n]+)',
                 'tendering_organization'),
                (r'Opportunity Size[:\s]*([^\\n]+)', 'opportunity_size'),
                (r'Deadline[:\s]*([^\\n]+)', 'deadline'),
                (r'Categories[:\s]*([^\\n]+)', 'categories'),
                (r'Topics[:\s]*([^\\n]+)', 'topics'),
                (r'Reference Number[:\s]*([^\\n]+)', 'reference_number'),
                (r'Official Title[:\s]*([^\\n]+)', 'official_title'),
                (r'Updated[:\s]*([^\\n]+)', 'updated')
            ]

            page_text = self.driver.page_source

            for pattern, field in key_value_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    # Clean HTML tags and extra whitespace
                    value = re.sub(r'<[^>]+>', '', matches[0])
                    value = re.sub(r'\s+', ' ', value).strip()
                    opportunity[field] = value

        except Exception as e:
            print(f"⚠️ Error extracting key information: {e}")

    def _extract_detailed_sections(self, opportunity: Dict):
        """Extract detailed content sections"""
        try:
            # Look for common section headers and their content
            section_patterns = [
                (r'Background[:\s]*([^\\n]*(?:\\n(?!\\b(?:Objective|Scope|Qualification|Documents|Performance|Payment|Submission)\\b)[^\\n]*)*)', 'background'),
                (r'Objective[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Scope|Qualification|Documents|Performance|Payment|Submission)\\b)[^\\n]*)*)', 'objective'),
                (r'Scope of Work[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Objective|Qualification|Documents|Performance|Payment|Submission)\\b)[^\\n]*)*)', 'scope_of_work'),
                (r'Qualification[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Objective|Scope|Documents|Performance|Payment|Submission)\\b)[^\\n]*)*)',
                 'qualification_requirements'),
                (r'Documents[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Objective|Scope|Qualification|Performance|Payment|Submission)\\b)[^\\n]*)*)', 'documents_required'),
                (r'Performance[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Objective|Scope|Qualification|Documents|Payment|Submission)\\b)[^\\n]*)*)', 'performance_evaluation'),
                (r'Payment[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Objective|Scope|Qualification|Documents|Performance|Submission)\\b)[^\\n]*)*)', 'payment_terms'),
                (r'Submission[:\s]*([^\\n]*(?:\\n(?!\\b(?:Background|Objective|Scope|Qualification|Documents|Performance|Payment)\\b)[^\\n]*)*)', 'submission_instructions')
            ]

            page_text = self.driver.find_element(By.TAG_NAME, 'body').text

            for pattern, field in section_patterns:
                matches = re.findall(pattern, page_text,
                                     re.IGNORECASE | re.DOTALL)
                if matches:
                    # Clean and limit the content
                    content = matches[0].strip()
                    content = re.sub(r'\s+', ' ', content)
                    opportunity[field] = content[:1000] + \
                        "..." if len(content) > 1000 else content

        except Exception as e:
            print(f"⚠️ Error extracting detailed sections: {e}")

    def _go_to_next_page(self) -> bool:
        """Navigate to the next page of results"""
        try:
            # Look for next page button
            next_selectors = [
                'a[aria-label="Next"]',
                '.next',
                '.pagination-next',
                'a[href*="page="]',
                'button[aria-label*="next"]',
                '.pager-next'
            ]

            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    if next_button.is_enabled() and next_button.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", next_button)
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue

            return False

        except Exception as e:
            print(f"⚠️ Error navigating to next page: {e}")
            return False

    def export_to_google_sheets(self) -> bool:
        """Export detailed opportunities to Google Sheets"""
        try:
            if not self.sheet:
                print("❌ Google Sheets not configured. Cannot export.")
                return False

            if not self.scraped_opportunities:
                print("⚠️ No opportunities to export")
                return False

            print(
                f"📤 Exporting {len(self.scraped_opportunities)} detailed opportunities to Google Sheets...")

            # Prepare data for batch update
            rows_to_add = []

            for opp in self.scraped_opportunities:
                row = [
                    opp.get('title', ''),
                    opp.get('official_title', ''),
                    opp.get('type', ''),
                    opp.get('status', ''),
                    opp.get('updated', ''),
                    opp.get('funded_by', ''),
                    opp.get('tendering_organization', ''),
                    opp.get('location', ''),
                    opp.get('opportunity_size', ''),
                    opp.get('deadline', ''),
                    opp.get('categories', ''),
                    opp.get('topics', ''),
                    opp.get('reference_number', ''),
                    opp.get('background', ''),
                    opp.get('objective', ''),
                    opp.get('scope_of_work', ''),
                    opp.get('qualification_requirements', ''),
                    opp.get('documents_required', ''),
                    opp.get('performance_evaluation', ''),
                    opp.get('payment_terms', ''),
                    opp.get('submission_instructions', ''),
                    opp.get('additional_information', ''),
                    opp.get('url', ''),
                    opp.get('scraped_at', '')
                ]
                rows_to_add.append(row)

            # Add all rows at once
            if rows_to_add:
                self.sheet.append_rows(rows_to_add)
                print(
                    f"✅ Successfully exported {len(rows_to_add)} detailed opportunities to Google Sheets")

                # Get the spreadsheet URL
                spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{self.sheet.spreadsheet.id}"
                print(f"🔗 Spreadsheet URL: {spreadsheet_url}")

                return True

        except Exception as e:
            print(f"❌ Error exporting to Google Sheets: {e}")
            return False

    def save_to_json(self, filename: str = None) -> str:
        """Save detailed opportunities to JSON file"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"devex_detailed_opportunities_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_opportunities': len(self.scraped_opportunities),
                    'login_used': self.logged_in,
                    'opportunities': self.scraped_opportunities
                }, f, indent=2, ensure_ascii=False)

            print(
                f"💾 Saved {len(self.scraped_opportunities)} detailed opportunities to {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
            return ""

    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")


def main():
    """Main function to run the enhanced scraper"""
    print("🚀 DEVEX ENHANCED VIDEO OPPORTUNITIES SCRAPER")
    print("=" * 60)

    # Configuration - Get from environment variables
    EMAIL = "dre@whattookyousolong.org"
    PASSWORD = "whysolong"
    GOOGLE_CREDENTIALS_PATH = "google-credentials.json"  # Update this path if needed
    SPREADSHEET_ID = "1hCmLJ3h7RJdofji77YGyBqPnnq0vMmvvGYyHMyE7R5M"  # Your Google Sheets ID
    MAX_OPPORTUNITIES = 10  # Number of opportunities to scrape in detail

    # Initialize scraper
    scraper = DevexEnhancedScraper(EMAIL, PASSWORD, GOOGLE_CREDENTIALS_PATH)

    try:
        # Setup driver
        if not scraper.setup_driver():
            print("❌ Failed to setup driver. Exiting.")
            return

        # Login to Devex
        if not scraper.login():
            print("❌ Failed to login. Please check credentials. Exiting.")
            return

        # Setup Google Sheets (optional)
        sheets_configured = scraper.setup_google_sheets(SPREADSHEET_ID)

        # Navigate to search page
        if not scraper.navigate_to_search():
            print("❌ Failed to navigate to search page. Exiting.")
            return

        # Scrape opportunities with detailed information
        if scraper.scrape_opportunities_detailed(MAX_OPPORTUNITIES):
            print(
                f"✅ Successfully scraped {len(scraper.scraped_opportunities)} detailed opportunities")

            # Export to Google Sheets
            if sheets_configured:
                scraper.export_to_google_sheets()

            # Save to JSON as backup
            json_file = scraper.save_to_json()

            # Print summary
            print(f"\n📊 DETAILED SCRAPING SUMMARY:")
            print(
                f"Login successful: {'✅ Yes' if scraper.logged_in else '❌ No'}")
            print(f"Total opportunities: {len(scraper.scraped_opportunities)}")
            print(
                f"Google Sheets: {'✅ Exported' if sheets_configured else '❌ Not configured'}")
            print(f"JSON backup: {json_file}")

            # Show sample data
            if scraper.scraped_opportunities:
                print(f"\n📋 SAMPLE DETAILED OPPORTUNITY:")
                sample = scraper.scraped_opportunities[0]
                for key, value in sample.items():
                    if value:  # Only show fields with data
                        display_value = value[:100] + \
                            "..." if len(str(value)) > 100 else value
                        print(f"  {key}: {display_value}")

        else:
            print("❌ Detailed scraping failed")

    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        # Clean up
        scraper.close()
        print("\n✅ Enhanced scraping completed!")


if __name__ == "__main__":
    main()
