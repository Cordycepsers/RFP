import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io

# CONFIGURATION
DRIVE_FOLDER_ID = '1jz0IBiLLU25MSyzP_SSo0Q3TrBlEnheF'  # Google Drive folder ID
LOCAL_FOLDER = './UNDP-LKA-00546,1/'
SERVICE_ACCOUNT_FILE = 'src/advanced_scrapers/google-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate and build service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Ensure local folder exists
os.makedirs(LOCAL_FOLDER, exist_ok=True)

def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, mimeType)').execute()
    return results.get('files', [])

def download_file(service, file_id, file_name, mime_type, local_folder):
    # Handle Google Docs, Sheets, Slides export
    export_mime_map = {
        'application/vnd.google-apps.document': ('application/pdf', '.pdf'),
        'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
        'application/vnd.google-apps.presentation': ('application/pdf', '.pdf'),
    }
    if mime_type in export_mime_map:
        export_mime, ext = export_mime_map[mime_type]
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        file_name = file_name + ext
    else:
        request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(os.path.join(local_folder, file_name), 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Downloading {file_name}: {int(status.progress() * 100)}%")
    fh.close()

def main():
    files = list_files_in_folder(drive_service, DRIVE_FOLDER_ID)
    if not files:
        print("No files found in the Google Drive folder.")
        return
    for file in files:
        print(f"Downloading {file['name']}...")
        download_file(drive_service, file['id'], file['name'], file.get('mimeType', ''), LOCAL_FOLDER)
    print("All files downloaded to:", LOCAL_FOLDER)

if __name__ == '__main__':
    main()
