import hashlib
import json
import os
from unittest.mock import MagicMock, call, patch

import pytest

from dashboard.src.utils.helpers import _get, delete_files, get_hash, get_version


class TestGet:

    def test_simple_key(self):
        data = {"temperature": {"value": 72}}
        assert _get(data, "temperature") == 72

    def test_nested_keys(self):
        data = {"a": {"b": {"value": 42}}}
        assert _get(data, "a", "b") == 42

    def test_missing_key_returns_none(self):
        data = {"a": {"value": 1}}
        assert _get(data, "missing") is None

    def test_deeply_missing_returns_none(self):
        data = {"a": {"b": {"value": 1}}}
        assert _get(data, "a", "missing") is None

    def test_empty_dict(self):
        assert _get({}, "a") is None

    def test_no_value_key(self):
        data = {"temperature": {"unit": "F"}}
        assert _get(data, "temperature") is None


class TestGetHash:

    def test_deterministic(self):
        obj = {"a": 1, "b": 2}
        assert get_hash(obj) == get_hash(obj)

    def test_different_objects(self):
        assert get_hash({"a": 1}) != get_hash({"a": 2})

    def test_order_independent(self):
        assert get_hash({"b": 2, "a": 1}) == get_hash({"a": 1, "b": 2})

    def test_returns_hex_string(self):
        result = get_hash({"test": True})
        assert len(result) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in result)


class TestDeleteFiles:

    @patch("os.remove")
    def test_deletes_files(self, mock_remove):
        delete_files(["/tmp/a.txt", "/tmp/b.txt"])
        assert mock_remove.call_count == 2
        mock_remove.assert_any_call("/tmp/a.txt")
        mock_remove.assert_any_call("/tmp/b.txt")

    @patch("os.remove", side_effect=FileNotFoundError)
    def test_handles_not_found(self, mock_remove):
        delete_files(["/tmp/missing.txt"])  # Should not raise

    @patch("os.remove", side_effect=PermissionError)
    def test_handles_permission_error(self, mock_remove):
        delete_files(["/tmp/locked.txt"])  # Should not raise

    @patch("os.remove", side_effect=OSError("disk error"))
    def test_handles_os_error(self, mock_remove):
        delete_files(["/tmp/error.txt"])  # Should not raise

    @patch("os.remove")
    def test_empty_list(self, mock_remove):
        delete_files([])
        mock_remove.assert_not_called()


class TestGetVersion:

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="1.5.0\n")
    def test_returns_version(self, mock_read, mock_exists):
        result = get_version()
        assert result == "1.5.0"

    @patch("pathlib.Path.exists", return_value=False)
    def test_file_not_found(self, mock_exists):
        result = get_version()
        assert result is None
