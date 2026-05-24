import json
import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.tasks import convert_latex_to_images, normalize, tasks


class TestNormalize:

    def test_strip_leading_numbering(self):
        assert normalize("2. x + 3 = 5") == "x + 3 = 5"

    def test_strip_dollar_signs(self):
        assert normalize("$x^2$") == "x^2"

    def test_strip_paren_delimiters(self):
        assert normalize(r"\(x + 1\)") == "x + 1"

    def test_strip_bracket_delimiters(self):
        assert normalize(r"\[x + 1\]") == "x + 1"

    def test_combined(self):
        assert normalize(r"3. $\(x^2\)$") == "x^2"

    def test_plain_text(self):
        assert normalize("hello world") == "hello world"

    def test_strips_whitespace(self):
        assert normalize("  x + 1  ") == "x + 1"

    def test_numbering_with_spaces(self):
        assert normalize("  10. expression") == "expression"


class TestConvertLatexToImages:

    @patch("dashboard.src.tasks.get_storage_client")
    @patch("dashboard.src.tasks.latex_to_png")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_converts_latex_to_image(
        self, mock_remove, mock_exists, mock_latex, mock_storage
    ):
        mock_exists.return_value = True
        mock_storage_client = MagicMock()
        mock_storage_client.upload_file.return_value = "http://minio/problems/abc.png"
        mock_storage.return_value = mock_storage_client

        problems = [{"elements": [{"kind": "latex", "content": "$x^2$"}]}]
        result = convert_latex_to_images(problems)
        assert result[0]["elements"][0]["kind"] == "image"
        assert "problems/" in result[0]["elements"][0]["content"]

    @patch("dashboard.src.tasks.get_storage_client")
    @patch("dashboard.src.tasks.latex_to_png")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_skips_non_latex(self, mock_remove, mock_exists, mock_latex, mock_storage):
        problems = [{"elements": [{"kind": "text", "content": "hello"}]}]
        result = convert_latex_to_images(problems)
        assert result[0]["elements"][0]["kind"] == "text"
        mock_latex.assert_not_called()

    @patch("dashboard.src.tasks.get_storage_client")
    @patch("dashboard.src.tasks.latex_to_png")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_keeps_original_on_failure(
        self, mock_remove, mock_exists, mock_latex, mock_storage
    ):
        mock_exists.return_value = True
        mock_storage_client = MagicMock()
        mock_storage_client.upload_file.side_effect = Exception("upload failed")
        mock_storage.return_value = mock_storage_client

        problems = [{"elements": [{"kind": "latex", "content": "x^2"}]}]
        result = convert_latex_to_images(problems)
        # Should keep original since conversion failed
        assert result[0]["elements"][0]["kind"] == "latex"

    @patch("dashboard.src.tasks.get_storage_client")
    @patch("dashboard.src.tasks.latex_to_png")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_skips_when_png_not_created(
        self, mock_remove, mock_exists, mock_latex, mock_storage
    ):
        mock_exists.return_value = False
        mock_storage.return_value = MagicMock()

        problems = [{"elements": [{"kind": "latex", "content": "x^2"}]}]
        result = convert_latex_to_images(problems)
        assert result[0]["elements"][0]["kind"] == "latex"


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["message_broker_client"] = MagicMock()
    return app


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(app, mock_db):
    app.register_blueprint(tasks, url_prefix="/tasks")

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


class TestPrintTasksEndpoint:

    @patch("dashboard.src.tasks.print_tasks")
    def test_success(self, mock_pt, client, app):
        mock_pt.return_value = {"title": "Tasks", "items": ["Do stuff"]}
        resp = client.get("/tasks/print")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
        app.config["message_broker_client"].send_message.assert_called_once()
