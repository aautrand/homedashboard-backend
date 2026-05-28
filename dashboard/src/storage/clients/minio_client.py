import os
from logging import getLogger
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from dashboard.src.storage.clients.base import StorageClient

logger = getLogger(__name__)


class MinIOClient(StorageClient):
    """MinIO storage client using the official SDK."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse endpoint URL to extract host and determine SSL
        endpoint_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        parsed = urlparse(endpoint_url)

        # Extract host:port (remove scheme)
        self.endpoint = parsed.netloc or parsed.path
        self.secure = parsed.scheme == "https"
        self.base_url = endpoint_url

        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = os.getenv("MINIO_BUCKET", "printer-images")

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

    def _ensure_bucket(self, bucket: str) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info(f"Created bucket: {bucket}")
        except S3Error as e:
            logger.error(f"Failed to create bucket {bucket}: {e}")
            raise

    def upload_file(
        self, local_path: str, remote_path: str = None, bucket: str = None
    ) -> str:
        """
        Upload a file to MinIO.

        Args:
            local_path: Path to local file
            remote_path: Optional destination path (defaults to basename of local_path)
            bucket: Optional bucket name (defaults to configured bucket)

        Returns:
            URL to uploaded file
        """
        if remote_path is None:
            remote_path = os.path.basename(local_path)

        bucket = bucket or self.bucket

        try:
            self._ensure_bucket(bucket)

            self.client.fput_object(bucket, remote_path, local_path)
            logger.info(
                f"Uploaded {local_path} to MinIO as {remote_path} in bucket {bucket}"
            )

            return f"{self.base_url}/{bucket}/{remote_path}"

        except S3Error as e:
            logger.error(f"Failed to upload {local_path} to MinIO: {e}")
            raise

    def download_file(
        self, remote_path: str, local_path: str, bucket: str = None
    ) -> None:
        """
        Download a file from MinIO.

        Args:
            remote_path: Path in MinIO
            local_path: Destination path on local filesystem
            bucket: Optional bucket name (defaults to configured bucket)
        """
        bucket = bucket or self.bucket

        try:
            self.client.fget_object(bucket, remote_path, local_path)
            logger.info(f"Downloaded {remote_path} from MinIO to {local_path}")

        except S3Error as e:
            logger.error(f"Failed to download {remote_path} from MinIO: {e}")
            raise

    def read_file(self, remote_path: str, bucket: str = None) -> bytes:
        """
        Read a file from MinIO and return its contents as bytes.

        Args:
            remote_path: Path in MinIO
            bucket: Optional bucket name (defaults to configured bucket)
        """
        bucket = bucket or self.bucket
        try:
            response = self.client.get_object(bucket, remote_path)
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to read {remote_path} from MinIO: {e}")
            raise

    def delete_file(self, remote_path: str, bucket: str = None) -> None:
        """
        Delete a file from MinIO.

        Args:
            remote_path: Path in MinIO
            bucket: Optional bucket name (defaults to configured bucket)
        """
        bucket = bucket or self.bucket

        try:
            self.client.remove_object(bucket, remote_path)
            logger.info(f"Deleted {remote_path} from MinIO")

        except S3Error as e:
            logger.error(
                f"Failed to delete {remote_path} from MinIO: {e}"  # nosec B608
            )
            raise
