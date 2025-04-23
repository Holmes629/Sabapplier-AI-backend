# dropbox_storage.py
import dropbox
import requests
from django.core.files.storage import Storage
from django.conf import settings

class DropboxStorage(Storage):
    def __init__(self):
        self.client = dropbox.Dropbox(self.get_fresh_dropbox_access_token())
    
    def get_fresh_dropbox_access_token(self):
        url = "https://api.dropboxapi.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": settings.DROPBOX_REFRESH_TOKEN,
            "client_id": settings.DROPBOX_CLIENT_ID,
            "client_secret": settings.DROPBOX_CLIENT_SECRET,
        }

        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception("Failed to refresh Dropbox token: " + response.text)
        
    def get_available_name(self, name, max_length=None):
        # Always return the same name to enforce overwriting
        return name

    def _save(self, name, content):
        # Make sure path is valid
        name = name.replace("\\", "/")  # Normalize slashes
        name = name.strip("/")          # Remove leading/trailing slashes

        # Upload to Dropbox
        path = f"/{name}"
        try:
            self.client.files_upload(content.read(), path, mode=dropbox.files.WriteMode.overwrite)
            return name
        except dropbox.exceptions.ApiError as e:
            raise e  # Let Django handle the error


    def exists(self, name):
        try:
            self.client.files_get_metadata(f"/{name}")
            return True
        except dropbox.exceptions.ApiError:
            return False

    def url(self, name):
        dropbox_path = f"/{name}"
        try:
            # Ensure the file exists
            self.client.files_get_metadata(dropbox_path)

            # Try to create a new shared link
            shared_link_metadata = self.client.sharing_create_shared_link_with_settings(dropbox_path)
            return shared_link_metadata.url.replace("?dl=0", "?raw=1")

        except dropbox.exceptions.ApiError as e:
            # If shared link already exists, reuse it
            if (hasattr(e.error, "is_shared_link_already_exists") and e.error.is_shared_link_already_exists()):
                links = self.client.sharing_list_shared_links(path=dropbox_path, direct_only=True).links
                if links:
                    return links[0].url.replace("?dl=0", "?raw=1")

            # If file doesn't exist
            if (hasattr(e.error, "is_path") and e.error.get_path().is_not_found()):
                return ""  # or None or raise custom exception

            raise e  # For other unexpected errors


