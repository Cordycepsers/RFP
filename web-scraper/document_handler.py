#!/usr/bin/env python3

import os
import re
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import logging
import asyncio

class DocumentHandler:
    def __init__(self, download_dir="./downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def _find_elements_by_text_or_selector(self, page, selector, text_hints=None):
        """Find elements using CSS selector first, then fallback to text-based search"""
        try:
            # Try CSS selector first
            elements = await page.query_selector_all(selector)
            if elements:
                return elements
            
            # If no elements found and text hints provided, try text-based search
            if text_hints:
                for hint in text_hints:
                    try:
                        elements = await page.locator(f"text={hint}").all()
                        if elements:
                            return elements
                    except:
                        continue
            
            return []
        except Exception as e:
            print(f"Error finding elements: {e}")
            return []

    async def execute_document_workflow(self, page, website_config, project_id):
        """Execute document download workflow based on website configuration"""
        
        workflow_config = website_config.get('documentDownloadWorkflow', {})
        if not workflow_config.get('enabled', False):
            return []

        downloaded_docs = []

        if 'steps' in workflow_config:
            # Multi-step workflow (like UNDP)
            downloaded_docs = await self._execute_multi_step_workflow(page, workflow_config['steps'], project_id, website_config['name'])
        elif 'workflows' in workflow_config:
            # Multiple workflow types (like The Global Fund)
            downloaded_docs = await self._execute_multi_workflow(page, workflow_config['workflows'], project_id, website_config['name'])
        else:
            # Simple document extraction
            downloaded_docs = await self._extract_simple_documents(page, website_config, project_id)

        return downloaded_docs

    async def _execute_multi_step_workflow(self, page, steps, project_id, site_name):
        """Execute multi-step document workflow (UNDP style)"""
        downloaded_docs = []

        try:
            for step in steps:
                step_num = step['step']
                action = step['action']
                selector = step['selector']
                description = step.get('description', f'Step {step_num}')

                print(f"📋 Executing step {step_num}: {description}")

                if action == 'click_authentication_link':
                    # Click authentication link using enhanced finding
                    text_hints = ['this link', 'authentication', 'auth', 'login']
                    auth_elements = await self._find_elements_by_text_or_selector(page, selector, text_hints)
                    if auth_elements:
                        if step.get('opensNewTab', False):
                            async with page.context.expect_page() as new_page_info:
                                await auth_elements[0].click()
                            auth_page = await new_page_info.value
                            await asyncio.sleep(step.get('waitAfterClick', 2000) / 1000)
                            await auth_page.close()
                        else:
                            await auth_elements[0].click()
                            await asyncio.sleep(step.get('waitAfterClick', 2000) / 1000)

                elif action == 'click_document_list':
                    # Click to open document list using enhanced finding
                    text_hints = ['Negotiation Document(s)', 'Documents', 'Negotiation Documents', 'attachments']
                    doc_elements = await self._find_elements_by_text_or_selector(page, selector, text_hints)
                    if doc_elements:
                        if step.get('opensNewTab', False):
                            async with page.context.expect_page() as new_page_info:
                                await doc_elements[0].click()
                            doc_page = await new_page_info.value
                            await asyncio.sleep(step.get('waitAfterClick', 2000) / 1000)
                            # Continue with this page for document download
                            page = doc_page

                elif action == 'download_all_documents':
                    # Download all documents
                    doc_links = await page.query_selector_all(selector)
                    max_docs = step.get('maxDocuments', 10)
                    
                    for i, link in enumerate(doc_links[:max_docs]):
                        try:
                            href = await link.get_attribute('href')
                            if href:
                                full_url = urljoin(page.url, href)
                                filename = self._generate_filename(full_url, project_id, site_name, i)
                                
                                downloaded_file = self._download_file(full_url, filename)
                                if downloaded_file:
                                    downloaded_docs.append({
                                        'filename': filename,
                                        'local_path': downloaded_file,
                                        'source_url': full_url,
                                        'mime_type': self._get_mime_type(filename)
                                    })
                        except Exception as e:
                            print(f"❌ Error downloading document {i}: {e}")

        except Exception as e:
            print(f"❌ Error in multi-step workflow: {e}")

        return downloaded_docs

    async def _execute_multi_workflow(self, page, workflows, project_id, site_name):
        """Execute multiple workflow types (The Global Fund style)"""
        downloaded_docs = []

        try:
            for workflow in workflows:
                workflow_type = workflow['type']
                condition = workflow['condition']
                selector = workflow['selector']

                print(f"📋 Checking workflow: {workflow_type}")

                # Check if condition is met (simplified - you could make this more sophisticated)
                elements = await page.query_selector_all(selector)
                
                if elements:
                    print(f"✅ Found {len(elements)} documents for {workflow_type}")
                    
                    for i, element in enumerate(elements):
                        try:
                            href = await element.get_attribute('href')
                            if href:
                                full_url = urljoin(page.url, href)
                                filename = self._generate_filename(full_url, project_id, site_name, i, workflow_type)
                                
                                downloaded_file = self._download_file(full_url, filename)
                                if downloaded_file:
                                    downloaded_docs.append({
                                        'filename': filename,
                                        'local_path': downloaded_file,
                                        'source_url': full_url,
                                        'mime_type': self._get_mime_type(filename),
                                        'type': workflow_type
                                    })
                        except Exception as e:
                            print(f"❌ Error downloading {workflow_type} document {i}: {e}")

        except Exception as e:
            print(f"❌ Error in multi-workflow: {e}")

        return downloaded_docs

    async def _extract_simple_documents(self, page, website_config, project_id):
        """Extract documents using simple selectors"""
        downloaded_docs = []

        try:
            # Look for document selectors in the config
            doc_selectors = website_config.get('selectors', {}).get('documents', {})
            
            if 'downloadLinks' in doc_selectors:
                download_selector = doc_selectors['downloadLinks']
                doc_elements = await page.query_selector_all(download_selector)
                
                print(f"📋 Found {len(doc_elements)} documents using simple extraction")
                
                for i, element in enumerate(doc_elements):
                    try:
                        href = await element.get_attribute('href')
                        if href:
                            full_url = urljoin(page.url, href)
                            filename = self._generate_filename(full_url, project_id, website_config['name'], i)
                            
                            downloaded_file = self._download_file(full_url, filename)
                            if downloaded_file:
                                downloaded_docs.append({
                                    'filename': filename,
                                    'local_path': downloaded_file,
                                    'source_url': full_url,
                                    'mime_type': self._get_mime_type(filename)
                                })
                    except Exception as e:
                        print(f"❌ Error downloading document {i}: {e}")

        except Exception as e:
            print(f"❌ Error in simple document extraction: {e}")

        return downloaded_docs

    def _download_file(self, url, filename):
        """Download a file from URL to local storage"""
        try:
            print(f"📥 Downloading: {filename}")
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            file_path = self.download_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = file_path.stat().st_size
            print(f"✅ Downloaded: {filename} ({file_size / 1024:.1f} KB)")
            
            return str(file_path)

        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            return None

    def _generate_filename(self, url, project_id, site_name, index, doc_type=None):
        """Generate a filename for downloaded document"""
        
        # Extract original filename from URL
        parsed = urlparse(url)
        original_name = os.path.basename(parsed.path)
        
        if not original_name or '.' not in original_name:
            # Generate filename based on content-type or extension
            extension = self._guess_extension_from_url(url)
            original_name = f"document{extension}"

        # Clean the original filename
        clean_name = re.sub(r'[^\w\-_.]', '_', original_name)
        
        # Create structured filename
        site_prefix = re.sub(r'[^\w\-]', '_', site_name.lower())
        type_suffix = f"_{doc_type}" if doc_type else ""
        
        filename = f"{site_prefix}_{project_id}{type_suffix}_{index:02d}_{clean_name}"
        
        return filename

    def _guess_extension_from_url(self, url):
        """Guess file extension from URL"""
        common_docs = {
            'pdf': '.pdf',
            'doc': '.doc', 
            'docx': '.docx',
            'xls': '.xls',
            'xlsx': '.xlsx',
            'zip': '.zip',
            'rar': '.rar'
        }
        
        url_lower = url.lower()
        for ext_name, ext in common_docs.items():
            if ext_name in url_lower:
                return ext
                
        return '.pdf'  # Default to PDF

    def _get_mime_type(self, filename):
        """Get MIME type from filename"""
        extension = Path(filename).suffix.lower()
        
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.txt': 'text/plain'
        }
        
        return mime_types.get(extension, 'application/octet-stream')

    def cleanup_downloads(self, keep_files=False):
        """Clean up downloaded files"""
        if not keep_files:
            for file_path in self.download_dir.glob('*'):
                if file_path.is_file():
                    file_path.unlink()
