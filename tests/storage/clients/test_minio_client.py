from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error


class TestMinIOClient:

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def _make_client(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        client = MinIOClient()
        return client, mock_minio_cls.return_value

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_init_defaults(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        client = MinIOClient()
        mock_minio_cls.assert_called_once()
        assert client.bucket == "printer-images"

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_upload_file_default_remote_path(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.bucket_exists.return_value = True

        client = MinIOClient()
        result = client.upload_file("/tmp/test.png")
        assert "test.png" in result
        mock_minio.fput_object.assert_called_once()

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_upload_file_custom_remote_path(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.bucket_exists.return_value = True

        client = MinIOClient()
        result = client.upload_file("/tmp/test.png", "custom/path.png")
        assert "custom/path.png" in result

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_upload_file_custom_bucket(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.bucket_exists.return_value = True

        client = MinIOClient()
        result = client.upload_file("/tmp/test.png", "file.png", bucket="custom-bucket")
        assert "custom-bucket" in result

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_ensure_bucket_creates_if_not_exists(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.bucket_exists.return_value = False

        client = MinIOClient()
        client._ensure_bucket("new-bucket")
        mock_minio.make_bucket.assert_called_once_with("new-bucket")

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_ensure_bucket_skips_if_exists(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.bucket_exists.return_value = True

        client = MinIOClient()
        client._ensure_bucket("existing-bucket")
        mock_minio.make_bucket.assert_not_called()

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_download_file(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        client = MinIOClient()
        client.download_file("remote.png", "/tmp/local.png")
        mock_minio.fget_object.assert_called_once_with(
            "printer-images", "remote.png", "/tmp/local.png"
        )

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_download_file_custom_bucket(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        client = MinIOClient()
        client.download_file("remote.png", "/tmp/local.png", bucket="other")
        mock_minio.fget_object.assert_called_once_with(
            "other", "remote.png", "/tmp/local.png"
        )

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_delete_file(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        client = MinIOClient()
        client.delete_file("remote.png")
        mock_minio.remove_object.assert_called_once_with("printer-images", "remote.png")

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_delete_file_custom_bucket(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        client = MinIOClient()
        client.delete_file("remote.png", bucket="other")
        mock_minio.remove_object.assert_called_once_with("other", "remote.png")

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_upload_s3_error_raises(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.bucket_exists.return_value = True
        mock_minio.fput_object.side_effect = S3Error(
            "PutObject", "bucket", "object", "404", "Not Found", "req123"
        )

        client = MinIOClient()
        with pytest.raises(S3Error):
            client.upload_file("/tmp/test.png")

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_download_s3_error_raises(self, mock_minio_cls):
        from dashboard.src.storage.clients.minio_client import MinIOClient

        mock_minio = mock_minio_cls.return_value
        mock_minio.fget_object.side_effect = S3Error(
            "GetObject", "bucket", "object", "404", "Not Found", "req123"
        )

        client = MinIOClient()
        with pytest.raises(S3Error):
            client.download_file("remote.png", "/tmp/local.png")

    @patch("dashboard.src.storage.clients.minio_client.Minio")
    def test_is_storage_client(self, mock_minio_cls):
        from dashboard.src.storage.clients.base import StorageClient
        from dashboard.src.storage.clients.minio_client import MinIOClient

        client = MinIOClient()
        assert isinstance(client, StorageClient)
