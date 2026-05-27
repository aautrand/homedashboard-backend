import pytest

from dashboard.src.storage.clients.base import StorageClient, get_storage_client


class TestStorageClientABC:

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            StorageClient()

    def test_concrete_subclass(self):
        class FakeStorage(StorageClient):
            def upload_file(self, local_path, remote_path):
                return "url"

            def download_file(self, remote_path, local_path):
                pass

            def read_file(self, remote_path, bucket=None):
                return b""

            def delete_file(self, remote_path):
                pass

        client = FakeStorage()
        assert client.upload_file("a", "b") == "url"


class TestGetStorageClient:

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown storage source"):
            get_storage_client("unknown")

    def test_minio_source(self):
        from unittest.mock import MagicMock, patch

        with patch("dashboard.src.storage.clients.minio_client.Minio") as mock_minio:
            client = get_storage_client("minio")
            assert client is not None
