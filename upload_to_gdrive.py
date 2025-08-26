def delete_folder(service, folder_id):
    try:
        service.files().delete(fileId=folder_id, supportsAllDrives=True).execute()
        print(f'Deleted folder with ID: {folder_id}')
    except Exception as e:
        print(f'Error deleting folder {folder_id}: {e}')
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

import time
# CONFIGURATION
LOCAL_FOLDER = './output/iucn_documents/'  # Upload IUCN documents folders
DRIVE_FOLDER_NAME = os.environ.get('DRIVE_FOLDER_NAME', 'IUCN_Tenders_by_Reference')  # Name for the folder in Shared Drive (can override via env var)
DRIVE_ID = '0AHbM0SsjOuLRUk9PVA'  # Shared Drive ID
SERVICE_ACCOUNT_FILE = 'google-credentials.json'  # Path to your service account credentials
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate and build service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, drive_id, parent_id=None):
    # Search for folder in Shared Drive
    parent_query = f"'{parent_id}' in parents" if parent_id else "'root' in parents"
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and {parent_query}"
    results = service.files().list(q=query, spaces='drive', supportsAllDrives=True, includeItemsFromAllDrives=True, driveId=drive_id, corpora='drive', fields='files(id)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    # Create folder in Shared Drive
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id or drive_id]
    }
    folder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
    # Wait briefly to ensure folder is available for upload
    time.sleep(2)
    return folder.get('id')

def upload_folder_structure(service, local_folder, parent_folder_id, drive_id):
    """Upload entire folder structure including subdirectories."""
    for item_name in os.listdir(local_folder):
        local_item_path = os.path.join(local_folder, item_name)
        
        if os.path.isdir(local_item_path):
            # Create subdirectory in Google Drive
            subfolder_id = get_or_create_folder(service, item_name, drive_id, parent_folder_id)
            print(f'Created/found subfolder: {item_name}')
            
            # Recursively upload contents
            upload_folder_structure(service, local_item_path, subfolder_id, drive_id)
            
        elif os.path.isfile(local_item_path):
            # Upload file
            file_metadata = {
                'name': item_name,
                'parents': [parent_folder_id]
            }
            media = MediaFileUpload(local_item_path, resumable=True)
            try:
                service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
                print(f'Uploaded: {item_name}')
            except Exception as e:
                print(f'Error uploading {item_name}: {e}')

def upload_files_to_folder(service, folder_id, local_folder, drive_id):
    """Upload files and folders recursively."""
    upload_folder_structure(service, local_folder, folder_id, drive_id)

def get_shareable_link(service, folder_id):
    # Set folder to anyone with the link can view
    service.permissions().create(
        fileId=folder_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        },
        supportsAllDrives=True
    ).execute()
    folder = service.files().get(fileId=folder_id, fields='webViewLink', supportsAllDrives=True).execute()
    return folder.get('webViewLink')

def main():
    print('Starting upload to Shared Drive...')
    # Create main folder in correct Shared Drive
    folder_id = get_or_create_folder(drive_service, DRIVE_FOLDER_NAME, DRIVE_ID)
    print(f'Uploading folder structure from {LOCAL_FOLDER} to folder {DRIVE_FOLDER_NAME} in Shared Drive...')
    upload_files_to_folder(drive_service, folder_id, LOCAL_FOLDER, DRIVE_ID)
    link = get_shareable_link(drive_service, folder_id)
    print(f'Shareable Google Drive folder link: {link}')

if __name__ == '__main__':
    main()
