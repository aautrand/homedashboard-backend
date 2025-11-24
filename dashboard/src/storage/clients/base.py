from abc import ABC, abstractmethod


class StorageClient(ABC):
    """Base class for storage clients."""

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Upload a file to storage.

        Args:
            local_path: Path to local file
            remote_path: Destination path in storage

        Returns:
            URL or path to uploaded file
        """
        ...

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download a file from storage.

        Args:
            remote_path: Path in storage
            local_path: Destination path on local filesystem
        """
        ...

    @abstractmethod
    def delete_file(self, remote_path: str) -> None:
        """
        Delete a file from storage.

        Args:
            remote_path: Path in storage
        """
        ...


def get_storage_client(source: str = "minio") -> StorageClient:
    """Factory function to get a storage client."""
    if source == "minio":
        from .minio_client import MinIOClient
        return MinIOClient()
    else:
        raise ValueError(f"Unknown storage source: {source}")