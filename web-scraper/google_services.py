import os
import json
import csv
import io
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
import logging

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

class GoogleDriveService:
    def __init__(self):
        self.auth = None
        self.drive = None
        self.sheets = None
        self.base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1FGCuypq0uc2_5zrqvWaXVVRbjfcYdbWe')
        self.service_account_email = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')
        self.is_initialized = False

    async def initialize(self):
        """Initialize Google Drive service with authentication"""
        try:
            print('🔧 Initializing Google Drive service...')
            
            # Setup authentication
            if os.path.exists('credentials.json'):
                self.auth = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            else:
                # Use environment variables
                credentials_info = {
                    'type': 'service_account',
                    'project_id': os.getenv('GOOGLE_PROJECT_ID'),
                    'private_key': os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
                    'client_email': os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL'),
                    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token'
                }
                self.auth = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)

            # Initialize Google APIs
            self.drive = build('drive', 'v3', credentials=self.auth)
            self.sheets = build('sheets', 'v4', credentials=self.auth)

            # Test the connection
            await self.test_connection()

            self.is_initialized = True
            print('✅ Google Drive service initialized successfully')

        except Exception as error:
            print(f'❌ Failed to initialize Google Drive service: {error}')
            raise error

    async def test_connection(self):
        """Test Google Drive connection"""
        try:
            response = self.drive.about().get(fields='user, storageQuota').execute()
            print(f"🔗 Connected to Google Drive as: {response['user']['emailAddress']}")
            
            quota = response.get('storageQuota', {})
            if quota:
                used_gb = float(quota.get('usage', 0)) / (1024**3)
                limit_gb = float(quota.get('limit', 0)) / (1024**3) if quota.get('limit') else 'Unlimited'
                print(f"💾 Storage: {used_gb:.2f}GB used of {limit_gb}GB")

        except Exception as error:
            raise Exception(f"Google Drive connection test failed: {error}")

    def upload_task_results(self, task_id, results, options=None):
        """Upload task results to Google Drive"""
        if options is None:
            options = {}
            
        try:
            print(f"📤 Uploading task results for task: {task_id}")

            # Create task folder
            task_folder = self.create_task_folder(task_id, options.get('task_name'))
            uploaded_files = []

            # Upload CSV data
            if results.get('data'):
                csv_file = self.upload_csv_data(task_folder['id'], task_id, results['data'])
                uploaded_files.append(csv_file)

            # Upload JSON data
            json_file = self.upload_json_data(task_folder['id'], task_id, results)
            uploaded_files.append(json_file)

            # Upload documents if present
            if results.get('documents'):
                documents_folder = self.create_folder('Documents', task_folder['id'])
                document_files = self.upload_documents(documents_folder['id'], results['documents'])
                uploaded_files.extend(document_files)

            # Create summary report
            summary_file = self.create_summary_report(task_folder['id'], task_id, results.get('summary', {}))
            uploaded_files.append(summary_file)

            # Share with designated users
            if options.get('share_with'):
                self.share_folder(task_folder['id'], options['share_with'])

            return {
                'folder_id': task_folder['id'],
                'folder_link': task_folder['webViewLink'],
                'files': uploaded_files
            }

        except Exception as error:
            print(f"Failed to upload task results: {error}")
            raise error

    def create_task_folder(self, task_id, task_name=None):
        """Create task folder with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        folder_name = f"{timestamp}_{task_name or task_id}"

        try:
            folder = self.create_folder(folder_name, self.base_folder_id)
            print(f"📁 Created task folder: {folder_name}")
            return folder
        except Exception as error:
            raise Exception(f"Failed to create task folder: {error}")

    def create_folder(self, name, parent_id=None):
        """Create a folder in Google Drive"""
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]

            response = self.drive.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()

            return response
        except Exception as error:
            raise Exception(f"Failed to create folder '{name}': {error}")

    def upload_csv_data(self, folder_id, task_id, data):
        """Upload CSV data file"""
        try:
            csv_content = self.generate_csv(data)
            file_name = f"{task_id}_opportunities.csv"

            return self.upload_buffer(
                csv_content.encode('utf-8'),
                file_name,
                'text/csv',
                folder_id
            )
        except Exception as error:
            raise Exception(f"Failed to upload CSV data: {error}")

    def upload_json_data(self, folder_id, task_id, data):
        """Upload JSON data file"""
        try:
            file_name = f"{task_id}_complete_data.json"
            json_content = json.dumps(data, indent=2, default=str)

            return self.upload_buffer(
                json_content.encode('utf-8'),
                file_name,
                'application/json',
                folder_id
            )
        except Exception as error:
            raise Exception(f"Failed to upload JSON data: {error}")

    def upload_documents(self, folder_id, documents):
        """Upload documents from local storage"""
        uploaded_files = []

        for doc in documents:
            try:
                if doc.get('local_path') and os.path.exists(doc['local_path']):
                    with open(doc['local_path'], 'rb') as f:
                        file_buffer = f.read()
                    
                    uploaded_file = self.upload_buffer(
                        file_buffer,
                        doc['filename'],
                        doc.get('mime_type', 'application/octet-stream'),
                        folder_id
                    )
                    uploaded_files.append(uploaded_file)
            except Exception as error:
                print(f"Failed to upload document: {doc.get('filename', 'unknown')} - {error}")

        return uploaded_files

    def create_summary_report(self, folder_id, task_id, summary):
        """Create summary report as Google Sheet"""
        try:
            sheet_title = f"{task_id}_Summary_Report"

            response = self.sheets.spreadsheets().create(body={
                'properties': {
                    'title': sheet_title
                },
                'sheets': [
                    {'properties': {'title': 'Summary'}},
                    {'properties': {'title': 'Website Results'}}
                ]
            }).execute()

            spreadsheet_id = response['spreadsheetId']

            # Move to the task folder
            self.drive.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents='root',
                fields='id, parents'
            ).execute()

            # Populate with summary data
            self.populate_summary_sheet(spreadsheet_id, summary)

            return {
                'id': spreadsheet_id,
                'name': sheet_title,
                'webViewLink': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
                'type': 'application/vnd.google-apps.spreadsheet'
            }

        except Exception as error:
            raise Exception(f"Failed to create summary report: {error}")

    def populate_summary_sheet(self, spreadsheet_id, summary):
        """Populate Google Sheet with summary data"""
        try:
            # Summary sheet data
            summary_data = [
                ['Metric', 'Value'],
                ['Total Opportunities', summary.get('total_opportunities', 0)],
                ['Media Opportunities', summary.get('media_opportunities', 0)],
                ['Documents Downloaded', summary.get('documents_downloaded', 0)],
                ['Processing Time (minutes)', round((summary.get('processing_time', 0)) / 60)],
                ['Success Rate (%)', round(summary.get('success_rate', 0))]
            ]

            self.sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Summary!A1:B6',
                valueInputOption='RAW',
                body={'values': summary_data}
            ).execute()

            # Website results data
            if summary.get('website_results'):
                website_headers = [
                    'Website', 'Status', 'Items Found', 'Items Extracted',
                    'Documents', 'Errors', 'Processing Time (min)'
                ]

                website_data = [website_headers]
                for result in summary['website_results']:
                    website_data.append([
                        result.get('website_name', ''),
                        result.get('status', ''),
                        result.get('items_found', 0),
                        result.get('items_extracted', 0),
                        result.get('documents_downloaded', 0),
                        result.get('error_count', 0),
                        round((result.get('processing_time', 0)) / 60)
                    ])

                self.sheets.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'Website Results!A1:G{len(website_data)}',
                    valueInputOption='RAW',
                    body={'values': website_data}
                ).execute()

        except Exception as error:
            print(f"Failed to populate summary sheet: {error}")

    def upload_buffer(self, buffer, file_name, mime_type, parent_id):
        """Upload buffer to Google Drive"""
        try:
            file_metadata = {'name': file_name}
            if parent_id:
                file_metadata['parents'] = [parent_id]

            media = MediaIoBaseUpload(
                io.BytesIO(buffer),
                mimetype=mime_type,
                resumable=True
            )

            response = self.drive.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size'
            ).execute()

            print(f"📄 Uploaded: {file_name} ({len(buffer) / 1024:.1f} KB)")

            return {
                'id': response['id'],
                'name': response['name'],
                'webViewLink': response['webViewLink'],
                'webContentLink': response.get('webContentLink', ''),
                'size': response.get('size', ''),
                'type': mime_type
            }
        except Exception as error:
            raise Exception(f"Failed to upload {file_name}: {error}")

    def share_folder(self, folder_id, email_addresses):
        """Share folder with users"""
        try:
            for email in email_addresses:
                self.drive.permissions().create(
                    fileId=folder_id,
                    body={
                        'role': 'reader',
                        'type': 'user',
                        'emailAddress': email
                    },
                    sendNotificationEmail=True,
                    emailMessage='Media procurement data collection results are ready for review.'
                ).execute()

                print(f"🔗 Shared folder with: {email}")

        except Exception as error:
            print(f"Failed to share folder: {error}")
            raise error

    def generate_csv(self, data):
        """Generate CSV content from extracted data"""
        if not data:
            return 'No data available'

        # Get all possible columns from all items
        columns = set()
        for item in data:
            columns.update(item.keys())
        columns = sorted(list(columns))

        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()

    def get_status(self):
        """Get service status"""
        return {
            'initialized': self.is_initialized,
            'authenticated': bool(self.auth),
            'service_account_email': self.service_account_email,
            'base_folder_id': self.base_folder_id
        }

# Legacy functions for backward compatibility
def get_google_services():
    service = GoogleDriveService()
    service.initialize()
    return service.sheets, service.drive

def get_last_scraped_date(sheets_service, spreadsheet_id, sheet_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f'{sheet_name}!L:L').execute()
    values = result.get('values', [])
    if not values:
        return None
    return values[-1][0] if values[-1] else None

def append_to_sheet(sheets_service, spreadsheet_id, sheet_name, data):
    body = {'values': [data]}
    result = sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f'{sheet_name}!A1',
        valueInputOption='RAW',
        body=body).execute()
    return result

