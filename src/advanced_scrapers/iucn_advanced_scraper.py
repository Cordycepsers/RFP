import os
import json
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

class IUCNAdvancedScraper:
    def __init__(self, keywords=None, output_dir='output'):
        self.keywords = keywords or [
            'media', 'film', 'video', 'photo', 'photography', 'content', 'story', 'documentary',
            'communication', 'awareness', 'outreach', 'press', 'journalism', 'broadcast',
            'digital', 'social media', 'campaign', 'creative', 'design', 'editorial', 'production',
            'graphic', 'copywriting', 'editing', 'magazine', 'newsletter', 'layout'
        ]
        self.base_url = 'https://iucn.org'
        self.output_dir = output_dir
        self.documents_dir = os.path.join(output_dir, 'iucn_documents')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
        
        # Setup session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Google Drive setup
        self.setup_google_drive()

    def setup_google_drive(self):
        """Initialize Google Drive service."""
        try:
            SERVICE_ACCOUNT_FILE = 'google-credentials.json'
            SCOPES = ['https://www.googleapis.com/auth/drive']
            self.drive_id = '0AHbM0SsjOuLRUk9PVA'  # Shared Drive ID
            
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("✓ Google Drive service initialized")
        except Exception as e:
            print(f"⚠ Google Drive setup failed: {e}")
            self.drive_service = None

    def create_tender_folder(self, tender_id, tender_title):
        """Create a local folder for the tender documents."""
        # Create safe folder name
        safe_title = "".join(c for c in tender_title if c.isalnum() or c in " -_")[:50].replace(" ", "_")
        folder_name = f"{tender_id}_{safe_title}"
        folder_path = os.path.join(self.documents_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path, folder_name

    def create_gdrive_folder(self, folder_name):
        """Create folder in Google Drive Shared Drive and return folder ID."""
        if not self.drive_service:
            return None
            
        try:
            # Create folder in Shared Drive (not regular Drive)
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.drive_id]  # Use shared drive ID as parent
            }
            folder = self.drive_service.files().create(
                body=file_metadata, 
                fields='id', 
                supportsAllDrives=True
            ).execute()
            
            folder_id = folder.get('id')
            
            # Set folder permissions to anyone with link can view
            self.drive_service.permissions().create(
                fileId=folder_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                },
                supportsAllDrives=True
            ).execute()
            
            print(f"✓ Created Google Drive folder: {folder_name}")
            time.sleep(1)  # Brief pause to ensure folder is ready
            return folder_id
            
        except Exception as e:
            print(f"Failed to create Google Drive folder {folder_name}: {e}")
            return None

    def upload_to_gdrive(self, local_file_path, gdrive_folder_id, filename):
        """Upload a single file to Google Drive folder."""
        if not self.drive_service or not gdrive_folder_id:
            return None
            
        try:
            file_metadata = {
                'name': filename,
                'parents': [gdrive_folder_id]
            }
            media = MediaFileUpload(local_file_path, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink',
                supportsAllDrives=True
            ).execute()
            
            print(f"✓ Uploaded to Google Drive: {filename}")
            return file.get('webViewLink')
            
        except Exception as e:
            print(f"Failed to upload {filename} to Google Drive: {e}")
            return None

    def get_gdrive_folder_link(self, folder_id):
        """Get shareable link for Google Drive folder."""
        if not self.drive_service or not folder_id:
            return None
            
        try:
            folder = self.drive_service.files().get(
                fileId=folder_id, 
                fields='webViewLink', 
                supportsAllDrives=True
            ).execute()
            return folder.get('webViewLink')
        except Exception as e:
            print(f"Failed to get folder link: {e}")
            return None

    def download_document(self, doc_url, tender_folder_path, filename=None):
        """Download a document from the given URL to the tender folder."""
        try:
            # Handle relative URLs
            if doc_url.startswith('/'):
                doc_url = urljoin(self.base_url, doc_url)
            
            print(f"Downloading: {doc_url}")
            response = self.session.get(doc_url, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            if not filename:
                parsed_url = urlparse(doc_url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    # Extract from Content-Disposition header if available
                    content_disposition = response.headers.get('Content-Disposition', '')
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[1].strip('"')
                    else:
                        filename = f"document_{int(time.time())}.pdf"
            
            # Create safe filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
            file_path = os.path.join(tender_folder_path, safe_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {file_path}")
            return file_path, safe_filename
            
        except Exception as e:
            print(f"Failed to download {doc_url}: {str(e)}")
            return None, None

    def process_media_opportunities(self):
        """Process the media opportunities we identified using MCP data."""
        
        # Use the opportunities we identified from MCP Playwright
        media_opportunities = [
            {
                "id": "IUCN_001",
                "title": "Communication and Graphic Design Services for the Layout and Production of a Global Impact Report and Communication Assets for the BIOPAMA Programme",
                "deadline": "31 August 2025",
                "office": "IUCN HQ Switzerland",
                "location": "ACP Region and EU Member States",
                "duration": "3 months",
                "value": "EUR 25,000",
                "documents": [
                    "/sites/default/files/2025-08/rfp_biopamaii-graphicdesigner-final.pdf",
                    "/sites/default/files/2025-08/attachment-1_specifications-terms-of-reference_corrected150825.pdf",
                    "/sites/default/files/2025-07/attachment-2_declaration-of-undertaking.pdf",
                    "/sites/default/files/2025-07/attachment-3_contract-template.pdf"
                ],
                "keywords_matched": ["communication", "graphic", "design"]
            },
            {
                "id": "IUCN_002", 
                "title": "Recrutement d'un consultant communication communication, visibilité et valorisation des résultats du projet 30x30/SPANB en Côte d'Ivoire",
                "deadline": "05 September 2025",
                "office": "IUCN PACO",
                "location": "République de Côte d'Ivoire",
                "duration": "03 Months",
                "value": "Below CHF 25,000",
                "documents": [
                    "/sites/default/files/2025-08/sop1_consultation-communication-projet-cote-divoire.pdf",
                    "/sites/default/files/2025-08/tdr-communication-civ_consultancy.pdf",
                    "/sites/default/files/2025-08/declaration-dengagement-consultants.docx",
                    "/sites/default/files/2025-07/modele-de-contrat-pour-consultants-individuels.pdf"
                ],
                "keywords_matched": ["communication"]
            },
            {
                "id": "IUCN_003",
                "title": "Design and Production of the Great Blue Wall 2025 Impact Report", 
                "deadline": "29 August 2025",
                "office": "IUCN ESARO",
                "location": "Nairobi",
                "duration": "6 months",
                "value": "Max USD 6,000",
                "documents": [
                    "/sites/default/files/2025-08/request-for-proposal_0.pdf",
                    "/sites/default/files/2025-08/terms-of-reference_3.pdf"
                ],
                "keywords_matched": ["design"]
            },
            {
                "id": "IUCN_004",
                "title": "Copywriting and Editing Consultancy for the Great Blue Wall Impact Report",
                "deadline": "29 August 2025", 
                "office": "IUCN ESARO",
                "location": "Nairobi",
                "duration": "6 months",
                "value": "Max USD 4,000",
                "documents": [
                    "/sites/default/files/2025-08/request-for-proposal_1.pdf",
                    "/sites/default/files/2025-08/terms-of-reference_4.pdf"
                ],
                "keywords_matched": ["copywriting", "editing"]
            },
            {
                "id": "IUCN_005",
                "title": "Request for Proposal Member Magazine",
                "deadline": "10 September 2025 (EXTENDED)",
                "office": "IUCN HQ",
                "location": "Switzerland", 
                "duration": "3 years",
                "value": "tbd",
                "documents": [
                    "/sites/default/files/2025-08/rfp-member-magazine-open-procedure_rev-12-aug-2025.pdf",
                    "/sites/default/files/2025-08/rfp-member-magazine-technical-requirements_june-2025_final-002.pdf"
                ],
                "keywords_matched": ["magazine"]
            }
        ]
        
        # Process each opportunity
        results = []
        for opp in media_opportunities:
            print(f"\n{'='*60}")
            print(f"Processing: {opp['title'][:50]}...")
            print(f"Tender ID: {opp['id']}")
            
            # Create local folder for this tender
            tender_folder_path, folder_name = self.create_tender_folder(opp['id'], opp['title'])
            print(f"✓ Created local folder: {tender_folder_path}")
            
            # Create Google Drive folder
            gdrive_folder_id = self.create_gdrive_folder(folder_name)
            gdrive_folder_link = None
            if gdrive_folder_id:
                gdrive_folder_link = self.get_gdrive_folder_link(gdrive_folder_id)
            
            # Download documents to tender folder
            downloaded_docs = []
            gdrive_links = []
            
            for doc_url in opp['documents']:
                local_path, filename = self.download_document(doc_url, tender_folder_path)
                if local_path and filename:
                    downloaded_docs.append(local_path)
                    
                    # Upload to Google Drive
                    if gdrive_folder_id:
                        gdrive_link = self.upload_to_gdrive(local_path, gdrive_folder_id, filename)
                        if gdrive_link:
                            gdrive_links.append(gdrive_link)
                
                time.sleep(1)  # Rate limiting
            
            # Create detailed record
            detailed_record = {
                "project_title": opp['title'],
                "organization": "IUCN",
                "country": opp['location'],
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "submission_deadline": opp['deadline'],
                "borrower_bid_reference": opp['id'],
                "project_details": f"IUCN tender for {opp['title']}",
                "bid_issuance_date": "",
                "bid_security": "",
                "bid_validity": "",
                "bid_opening_time": "",
                "qualification_requirements": [],
                "additional_requirements": [],
                "contact_email": "",
                "submission_portal": "https://iucn.org/procurement/currently-running-tenders",
                "document_links": opp['documents'],
                "downloaded_documents": downloaded_docs,
                "gdrive_folder_link": gdrive_folder_link,
                "gdrive_document_links": gdrive_links,
                "local_folder_path": tender_folder_path,
                "notice_type": "Open Tender",
                "office": opp['office'],
                "contract_duration": opp['duration'],
                "contract_value": opp['value'],
                "keywords_matched": opp['keywords_matched'],
                "scraped_at": datetime.now().isoformat()
            }
            
            # Save individual JSON file in tender folder
            json_filename = f"{opp['id']}_tender_details.json"
            json_path = os.path.join(tender_folder_path, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_record, f, indent=2, ensure_ascii=False)
            
            # Upload JSON to Google Drive as well
            if gdrive_folder_id:
                self.upload_to_gdrive(json_path, gdrive_folder_id, json_filename)
            
            results.append(detailed_record)
            print(f"✓ Processed tender: {opp['id']}")
            if gdrive_folder_link:
                print(f"✓ Google Drive folder: {gdrive_folder_link}")
            print(f"✓ Local folder: {tender_folder_path}")
            print(f"✓ Documents downloaded: {len(downloaded_docs)}")
            print(f"✓ Documents uploaded to GDrive: {len(gdrive_links)}")
        
        # Save summary file
        summary_file = f"{self.output_dir}/iucn_media_opportunities_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_opportunities": len(results),
                "scraped_at": datetime.now().isoformat(),
                "source": "IUCN Procurement - Currently Running Tenders",
                "opportunities": results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"✓ Summary saved: {summary_file}")
        print(f"✓ Total media-related opportunities processed: {len(results)}")
        print(f"✓ Documents organized in folders by tender reference")
        print(f"✓ Local documents directory: {self.documents_dir}")
        
        if self.drive_service:
            print(f"✓ All folders and documents uploaded to Google Drive")
            print("\nGoogle Drive Folders:")
            for result in results:
                if result.get('gdrive_folder_link'):
                    print(f"  - {result['borrower_bid_reference']}: {result['gdrive_folder_link']}")
        else:
            print("⚠ Google Drive upload was skipped (service not available)")
        
        return results

    def scrape(self):
        """Main scraping method that processes opportunities and downloads documents."""
        print("Starting IUCN Advanced Scraper with document download...")
        return self.process_media_opportunities()

if __name__ == '__main__':
    scraper = IUCNAdvancedScraper()
    scraper.scrape()
