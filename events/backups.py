import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery
import pickle
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import zipfile
from pathlib import Path
import threading
import json
import random
from dotenv import load_dotenv
load_dotenv()

MAX_BACKUPS = 3

class DriveAPI:
    def __init__(self, credentialsFile: str):
        self.credentials = credentialsFile
        self.__get_drive_service()

    def __get_drive_service(self):
        """Authenticates and returns the Google Drive API service instance"""
        creds = None
        tokenFile = '.driveAPItoken'


        if os.path.exists(tokenFile):
            with open(tokenFile, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '.gglcredentials', ['https://www.googleapis.com/auth/drive'])
                creds = flow.run_local_server(port=0)

            with open(tokenFile, 'wb') as token:
                pickle.dump(creds, token)

        self.service: googleapiclient.discovery.Resource = googleapiclient.discovery.build('drive', 'v3', credentials=creds)

    def upload_file(self, filename: str, folder_id: str = None) -> str:
        """Uploads a file to a specified Google Drive folder and returns its ID"""

        try:
            file_name = os.path.basename(filename)
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(filename, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return file.get('id')

        except HttpError as error:
            print(f"An API error occurred during upload: {error}")
        except FileNotFoundError:
            print(f"Error: Local file not found at '{filename}'")

        return None


    def delete_file(self, fileID: str):
        try:
            self.service.files().delete(fileId=fileID).execute()
            return True

        except HttpError as error:
            if error.resp.status == 404:
                print(f"Error: File ID '{fileID}' not found.")
            else:
                print(f"An API error occurred during deletion: {error}")
            return False
        

def compress_folder(folder: str, outputName: str) -> int:
    """
    Compresses a folder using built-in zipfile

    Returns the size of the archive.
    """

    folderPath = Path(folder)
    outputPath = Path(outputName)

    with zipfile.ZipFile(outputPath, "w", zipfile.ZIP_DEFLATED, compresslevel=5) as f:
        for file in folderPath.rglob("*"):
            if file.is_file():
                # Preserve folder structure inside the archive
                relativePath = file.relative_to(folderPath.parent)
                f.write(file, arcname=relativePath)

    filesize = outputPath.stat().st_size

    return filesize

drive = DriveAPI('.gglcredientals')


def backup_loop():
    threading.Timer(3600, backup_loop).start()

    # Get previous compression data
    if not os.path.exists('backup_ids.json'):
        with open('backup_ids.json', 'x') as f:
            f.write('[]')

    with open('backup_ids.json', 'r') as f:
        backupIDs: list[str] = json.load(f)

    numOfBackups = len(backupIDs)
    
    # Compress world first before uploading
    filename = f"backup{random.randint(1000000,9999999)}.zip"
    filesize = compress_folder('users', filename)


    # Upload to drive
    credfile = '../.gglcredentials'
    if os.path.exists(credfile):
        print(f"Credentials file '{credfile}' does not exist! Backup will not continue")
        return False
    
    drive = DriveAPI(credfile)

    # Delete previous backup if applicable
    if numOfBackups >= MAX_BACKUPS:
        drive.delete_file(backupIDs.pop(0))

    # Upload and save
    fileID = drive.upload_file(filename, os.getenv("FOLDER_ID"))
    backupIDs.append(fileID)

    with open('backup_ids.json', 'w') as f:
        json.dump(backupIDs, f)

    # Delete temp compressed folder
    os.remove(filename)    
    print(f"Compressed user data with a size of {(filesize / (1024**2)):.2f} MB and uploaded to drive!")

def start():
    try:
        backup_loop()
    except:
        from traceback import print_exc
        print_exc()
    