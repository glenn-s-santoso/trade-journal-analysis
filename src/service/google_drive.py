"""Google Drive service for uploading and managing trading report files."""

import os
from typing import Dict, Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.service.google_auth import ALL_SCOPES, GoogleAuthService


class GoogleDriveService:
    """Service for interacting with Google Drive API."""

    def __init__(self):
        """Initialize the Google Drive Service."""
        self.auth_service = GoogleAuthService(scopes=ALL_SCOPES)
        self.credentials = self.auth_service.get_credentials()
        self.drive_service = None

        if self.credentials:
            self.drive_service = build("drive", "v3", credentials=self.credentials)
        else:
            raise ValueError("Failed to obtain valid Google Drive credentials")

    def get_or_create_folder(
        self, folder_name: str, parent_folder_id: Optional[str] = None
    ) -> str:
        """Get folder ID by name or create it if it doesn't exist.

        Args:
            folder_name: Name of the folder to find or create
            parent_folder_id: ID of the parent folder (None for root)

        Returns:
            Folder ID
        """
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        response = (
            self.drive_service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )

        folders = response.get("files", [])

        # If folder exists, return its ID
        if folders:
            return folders[0]["id"]

        # Create folder if it doesn't exist
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_folder_id:
            folder_metadata["parents"] = [parent_folder_id]

        folder = (
            self.drive_service.files()
            .create(body=folder_metadata, fields="id")
            .execute()
        )

        return folder.get("id")

    def upload_file(
        self, file_path: str, folder_id: str, mime_type: Optional[str] = None
    ) -> Dict:
        """Upload a file to Google Drive.

        Args:
            file_path: Path to the file to upload
            folder_id: ID of the folder to upload to
            mime_type: MIME type of the file (optional)

        Returns:
            Dictionary containing file metadata (including id and webViewLink)
        """
        file_name = os.path.basename(file_path)

        # Auto-detect mime type if not provided
        if mime_type is None:
            if file_path.endswith(".png"):
                mime_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif file_path.endswith(".html"):
                mime_type = "text/html"
            elif file_path.endswith(".pdf"):
                mime_type = "application/pdf"
            else:
                mime_type = "application/octet-stream"

        # Check if file already exists in the folder
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        response = (
            self.drive_service.files()
            .list(q=query, spaces="drive", fields="files(id)")
            .execute()
        )

        existing_files = response.get("files", [])

        # If file exists, update it
        if existing_files:
            file_id = existing_files[0]["id"]
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            updated_file = (
                self.drive_service.files()
                .update(
                    fileId=file_id, media_body=media, fields="id, name, webViewLink"
                )
                .execute()
            )
            return updated_file

        # Otherwise create a new file
        file_metadata = {"name": file_name, "parents": [folder_id]}

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        file = (
            self.drive_service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )

        # Make the file publicly accessible with a link
        self.drive_service.permissions().create(
            fileId=file.get("id"), body={"role": "reader", "type": "anyone"}
        ).execute()

        # Get updated metadata with the webViewLink
        file = (
            self.drive_service.files()
            .get(fileId=file.get("id"), fields="id, name, webViewLink")
            .execute()
        )

        return file

    def upload_directory(
        self,
        local_dir: str,
        drive_folder_name: str,
        date_subfolder: Optional[str] = None,
    ) -> Dict[str, Dict]:
        """Upload an entire directory to Google Drive.

        Args:
            local_dir: Path to the local directory to upload
            drive_folder_name: Name of the main folder in Google Drive
            date_subfolder: Optional date subfolder name (e.g., '20230615_120000')

        Returns:
            Dictionary mapping filenames to their Drive metadata (including URLs)
        """
        # Get or create the main folder
        main_folder_id = self.get_or_create_folder(drive_folder_name)
        target_folder_id = main_folder_id

        # Create date subfolder if specified
        if date_subfolder:
            target_folder_id = self.get_or_create_folder(
                date_subfolder, parent_folder_id=main_folder_id
            )

        # Dictionary to store file metadata
        file_metadata_map = {}

        # Print directory structure for debugging
        print(f"Uploading directory: {local_dir}")

        # Walk through directory and upload all files
        for root, dirs, files in os.walk(local_dir):
            print(f"Scanning directory: {root}")
            print(f"Found subdirectories: {dirs}")
            print(f"Found files: {files}")

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, local_dir)
                print(f"Processing file: {file_path} (relative: {rel_path})")

                # Create subfolders if necessary
                current_folder_id = target_folder_id
                dir_path = os.path.dirname(rel_path)

                if dir_path and dir_path != ".":
                    # Handle subdirectory
                    print(f"Creating subfolder path: {dir_path}")
                    subfolders = dir_path.split(os.sep)

                    for subfolder in subfolders:
                        print(f"Creating/getting subfolder: {subfolder}")
                        current_folder_id = self.get_or_create_folder(
                            subfolder, parent_folder_id=current_folder_id
                        )

                # Upload the file
                print(f"Uploading file {file} to folder ID {current_folder_id}")
                file_metadata = self.upload_file(file_path, current_folder_id)
                file_metadata_map[rel_path] = file_metadata

        return file_metadata_map
