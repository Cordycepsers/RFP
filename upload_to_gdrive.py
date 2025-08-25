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
LOCAL_FOLDER = './output/'  # Upload all files from output directory
DRIVE_FOLDER_NAME = 'RFP_output_files'  # Name for the folder in Shared Drive
DRIVE_ID = '0AHbM0SsjOuLRUk9PVA'  # Shared Drive ID
SERVICE_ACCOUNT_FILE = 'src/advanced_scrapers/google-credentials.json'  # Path to your service account credentials
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate and build service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, drive_id):
    # Search for folder in Shared Drive root
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and 'root' in parents"
    results = service.files().list(q=query, spaces='drive', supportsAllDrives=True, includeItemsFromAllDrives=True, driveId=drive_id, corpora='drive', fields='files(id)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    # Create folder in Shared Drive root
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': ['root']
    }
    folder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
    # Wait briefly to ensure folder is available for upload
    time.sleep(2)
    return folder.get('id')

def upload_files_to_folder(service, folder_id, local_folder, drive_id):
    for filename in os.listdir(local_folder):
        file_path = os.path.join(local_folder, filename)
        if os.path.isfile(file_path):
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            try:
                service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
                print(f'Uploaded: {filename}')
            except Exception as e:
                print(f'Error uploading {filename}: {e}')

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
    # Delete old folder if it exists (ID: 1-z5ZjcTHGBKRuqtDmZc5RkjP12BKxvWU)
    delete_folder(drive_service, '1-z5ZjcTHGBKRuqtDmZc5RkjP12BKxvWU')
    # Create new folder in correct Shared Drive
    folder_id = get_or_create_folder(drive_service, DRIVE_FOLDER_NAME, DRIVE_ID)
    print(f'Uploading files from {LOCAL_FOLDER} to folder {DRIVE_FOLDER_NAME} in Shared Drive...')
    upload_files_to_folder(drive_service, folder_id, LOCAL_FOLDER, DRIVE_ID)
    link = get_shareable_link(drive_service, folder_id)
    print(f'Shareable Google Drive folder link: {link}')

if __name__ == '__main__':
    main()
