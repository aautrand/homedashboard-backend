from unittest.mock import MagicMock

from dashboard.src.ai.voice_query_manager import VoiceQueryManager


class TestVoiceQueryManager:
    def test_add_voice_query(self):
        db = MagicMock()

        voice_query = VoiceQueryManager(db).add_voice_query(
            filename="audio/a.wav", transcription="hi", response="hello"
        )

        db.add.assert_called_once_with(voice_query)
        assert voice_query.filename == "audio/a.wav"
        assert voice_query.transcription == "hi"
        assert voice_query.response == "hello"

    def test_is_processed_true_when_row_exists(self):
        db = MagicMock()
        db.execute.return_value.first.return_value = (1,)

        assert VoiceQueryManager(db).is_processed("audio/a.wav") is True

    def test_is_processed_false_when_missing(self):
        db = MagicMock()
        db.execute.return_value.first.return_value = None

        assert VoiceQueryManager(db).is_processed("audio/a.wav") is False
