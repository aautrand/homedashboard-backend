import os
from logging import getLogger

import requests
from flask import current_app

from dashboard.src.storage.clients.base import StorageClient

logger = getLogger(__name__)


class MinIOClient(StorageClient):
    """MinIO storage client using HTTP API."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Default to the mini service endpoint
        self.base_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9002")
        self.bucket = os.getenv("MINIO_BUCKET", "printer-images")

    def upload_file(self, local_path: str, remote_path: str = None) -> str:
        """
        Upload a file to MinIO.

        Args:
            local_path: Path to local file
            remote_path: Optional destination path (defaults to basename of local_path)

        Returns:
            URL to uploaded file
        """
        if remote_path is None:
            remote_path = os.path.basename(local_path)

        try:
            with open(local_path, "rb") as f:
                files = {"file": (remote_path, f)}
                data = {"bucket": self.bucket}
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
                response.raise_for_status()

            logger.info(f"Uploaded {local_path} to MinIO as {remote_path}")
            return f"{self.base_url}/{self.bucket}/{remote_path}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload {local_path} to MinIO: {e}")
            raise

    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download a file from MinIO.

        Args:
            remote_path: Path in MinIO
            local_path: Destination path on local filesystem
        """
        try:
            url = f"{self.base_url}/{self.bucket}/{remote_path}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded {remote_path} from MinIO to {local_path}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {remote_path} from MinIO: {e}")
            raise

    def delete_file(self, remote_path: str) -> None:
        """
        Delete a file from MinIO.

        Args:
            remote_path: Path in MinIO
        """
        try:
            data = {"bucket": self.bucket, "object_name": remote_path}
            response = requests.delete(
                f"{self.base_url}/delete",
                json=data,
                timeout=30
            )
            response.raise_for_status()

            logger.info(f"Deleted {remote_path} from MinIO")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete {remote_path} from MinIO: {e}")
            raise