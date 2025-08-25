"""
Google Drive integration for Proposaland monitoring system.
Handles automated upload of JSON/CSV reports to Google Drive.
"""

import json
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    logger.warning("Google Drive libraries not installed. Install with: pip install google-api-python-client google-auth")


class GoogleDriveUploader:
    """
    Google Drive uploader for Proposaland reports.
    Handles automated upload of daily reports and opportunities data.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.service = None
        self.folder_id = config.get('gdrive', {}).get('folder_id')
        self.credentials_file = config.get('gdrive', {}).get('credentials_file')
        
        if GOOGLE_DRIVE_AVAILABLE:
            self._authenticate()
        else:
            logger.error("Google Drive integration not available - missing dependencies")
    
    def _authenticate(self):
        """Authenticate with Google Drive API using service account."""
        try:
            if not self.credentials_file or not Path(self.credentials_file).exists():
                logger.error(f"Google Drive credentials file not found: {self.credentials_file}")
                return
            
            # Scopes for Google Drive API
            scopes = ['https://www.googleapis.com/auth/drive']
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive authentication successful")
            
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            self.service = None
    
    def upload_daily_report(self, file_paths: Dict[str, str], report_date: str) -> Dict[str, str]:
        """
        Upload daily report files to Google Drive.
        
        Args:
            file_paths: Dict with 'json_file', 'csv_file', 'summary_file' paths
            report_date: Date string for organizing files
            
        Returns:
            Dict with uploaded file IDs and URLs
        """
        if not self.service:
            logger.error("Google Drive service not available")
            return {}
        
        uploaded_files = {}
        
        try:
            # Create or get folder for the date
            date_folder_id = self._get_or_create_date_folder(report_date)
            
            # Upload each file
            for file_type, file_path in file_paths.items():
                if not file_path or not Path(file_path).exists():
                    logger.warning(f"File not found for upload: {file_path}")
                    continue
                
                file_id = self._upload_file(file_path, date_folder_id, file_type)
                if file_id:
                    file_url = f"https://drive.google.com/file/d/{file_id}/view"
                    uploaded_files[file_type] = {
                        'file_id': file_id,
                        'url': file_url,
                        'filename': Path(file_path).name
                    }
                    logger.info(f"Uploaded {file_type}: {Path(file_path).name}")
            
            logger.info(f"Daily report upload completed: {len(uploaded_files)} files")
            return uploaded_files
            
        except Exception as e:
            logger.error(f"Error uploading daily report: {e}")
            return {}
    
    def _get_or_create_date_folder(self, report_date: str) -> Optional[str]:
        """Get or create folder for the report date."""
        try:
            # Format folder name
            date_obj = datetime.strptime(report_date, '%Y%m%d')
            folder_name = f"Proposaland_{date_obj.strftime('%Y-%m-%d')}"
            
            # Check if folder exists
            existing_folder = self._find_folder(folder_name, self.folder_id)
            if existing_folder:
                return existing_folder
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            folder = self.service.files().create(body=folder_metadata).execute()
            logger.info(f"Created Google Drive folder: {folder_name}")
            return folder.get('id')
            
        except Exception as e:
            logger.error(f"Error creating date folder: {e}")
            return self.folder_id  # Fallback to main folder
    
    def _find_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Find existing folder by name."""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Error finding folder: {e}")
            return None
    
    def _upload_file(self, file_path: str, folder_id: Optional[str], file_type: str) -> Optional[str]:
        """Upload single file to Google Drive."""
        try:
            file_path_obj = Path(file_path)
            
            # Determine MIME type
            if file_path_obj.suffix.lower() == '.json':
                mime_type = 'application/json'
            elif file_path_obj.suffix.lower() == '.csv':
                mime_type = 'text/csv'
            else:
                mime_type = 'application/octet-stream'
            
            # File metadata
            file_metadata = {
                'name': file_path_obj.name,
                'parents': [folder_id] if folder_id else []
            }
            
            # Upload file
            media = MediaFileUpload(file_path, mimetype=mime_type)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return None
    
    def upload_opportunities_data(self, opportunities_data: Dict, filename: str) -> Optional[str]:
        """
        Upload opportunities data directly from memory.
        
        Args:
            opportunities_data: Formatted opportunities data
            filename: Name for the uploaded file
            
        Returns:
            File ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Google Drive service not available")
            return None
        
        try:
            # Convert data to JSON string
            json_data = json.dumps(opportunities_data, indent=2, ensure_ascii=False)
            
            # Create file-like object
            file_stream = io.BytesIO(json_data.encode('utf-8'))
            
            # File metadata
            file_metadata = {
                'name': f"{filename}.json",
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            # Upload from stream
            media = MediaIoBaseUpload(
                file_stream,
                mimetype='application/json',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"Uploaded opportunities data: {filename}.json")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Error uploading opportunities data: {e}")
            return None
    
    def create_sharing_link(self, file_id: str, permission_type: str = 'reader') -> Optional[str]:
        """
        Create shareable link for uploaded file.
        
        Args:
            file_id: Google Drive file ID
            permission_type: 'reader', 'writer', or 'commenter'
            
        Returns:
            Shareable URL if successful
        """
        if not self.service:
            return None
        
        try:
            # Create permission for anyone with link
            permission = {
                'type': 'anyone',
                'role': permission_type
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            # Get shareable link
            file_info = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return file_info.get('webViewLink')
            
        except Exception as e:
            logger.error(f"Error creating sharing link: {e}")
            return None
    
    def list_recent_uploads(self, days: int = 7) -> List[Dict]:
        """List recent uploads from the last N days."""
        if not self.service:
            return []
        
        try:
            # Calculate date threshold
            from datetime import timedelta
            threshold_date = datetime.now() - timedelta(days=days)
            threshold_str = threshold_date.isoformat() + 'Z'
            
            # Query recent files
            query = f"modifiedTime > '{threshold_str}'"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                orderBy='modifiedTime desc',
                fields='files(id, name, modifiedTime, webViewLink)'
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"Error listing recent uploads: {e}")
            return []
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """
        Clean up old files to manage storage.
        
        Args:
            days_to_keep: Number of days to keep files
            
        Returns:
            Number of files deleted
        """
        if not self.service:
            return 0
        
        try:
            # Calculate cutoff date
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.isoformat() + 'Z'
            
            # Find old files
            query = f"modifiedTime < '{cutoff_str}'"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            files_to_delete = results.get('files', [])
            deleted_count = 0
            
            for file_info in files_to_delete:
                try:
                    self.service.files().delete(fileId=file_info['id']).execute()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_info['name']}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_info['name']}: {e}")
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0


class GoogleDriveManager:
    """
    High-level manager for Google Drive operations.
    Combines upload and formatting functionality.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.uploader = GoogleDriveUploader(config)
        self.enabled = config.get('gdrive', {}).get('enabled', False) and GOOGLE_DRIVE_AVAILABLE
    
    def upload_daily_monitoring_report(self, all_website_data: List[Dict]) -> Dict[str, Any]:
        """
        Upload comprehensive daily monitoring report.
        
        Args:
            all_website_data: List of formatted data from all websites
            
        Returns:
            Upload results with file IDs and URLs
        """
        if not self.enabled:
            logger.info("Google Drive upload disabled or not available")
            return {}
        
        try:
            report_date = datetime.now().strftime('%Y%m%d')
            
            # Import here to avoid circular imports
            from src.outputs.enhanced_formatter import EnhancedOutputFormatter
            formatter = EnhancedOutputFormatter(self.config)
            
            # Create consolidated daily report
            report_file = formatter.create_daily_report(all_website_data)
            
            # Prepare files for upload
            file_paths = {
                'json_file': report_file,
                'csv_file': report_file.replace('.json', '.csv'),
                'summary_file': report_file.replace('.json', '_summary.json')
            }
            
            # Upload to Google Drive
            upload_results = self.uploader.upload_daily_report(file_paths, report_date)
            
            # Create sharing links
            for file_type, file_info in upload_results.items():
                sharing_link = self.uploader.create_sharing_link(file_info['file_id'])
                if sharing_link:
                    file_info['sharing_link'] = sharing_link
            
            logger.info(f"Daily monitoring report uploaded successfully")
            return upload_results
            
        except Exception as e:
            logger.error(f"Error uploading daily monitoring report: {e}")
            return {}
    
    def get_upload_status(self) -> Dict[str, Any]:
        """Get status of recent uploads and storage info."""
        if not self.enabled:
            return {'enabled': False, 'status': 'Google Drive integration disabled'}
        
        try:
            recent_files = self.uploader.list_recent_uploads(days=7)
            
            status = {
                'enabled': True,
                'authenticated': self.uploader.service is not None,
                'recent_uploads': len(recent_files),
                'recent_files': [
                    {
                        'name': f['name'],
                        'modified': f['modifiedTime'],
                        'url': f.get('webViewLink', '')
                    }
                    for f in recent_files[:5]  # Show last 5 files
                ]
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting upload status: {e}")
            return {'enabled': True, 'status': f'Error: {str(e)}'}
