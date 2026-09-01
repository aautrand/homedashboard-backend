from unittest.mock import patch

from dashboard.src.utils.helpers import env_flag


class TestEnvFlag:
    """Tests for boolean environment variable parsing."""

    @patch.dict("os.environ", {}, clear=True)
    def test_default_when_unset(self):
        """Test the default is returned when the variable is absent."""
        assert env_flag("MISSING") is True
        assert env_flag("MISSING", default=False) is False

    @patch.dict("os.environ", {"FLAG": "false"}, clear=True)
    def test_false_string(self):
        """Test 'false' switches the flag off."""
        assert env_flag("FLAG") is False

    @patch.dict("os.environ", {"FLAG": "true"}, clear=True)
    def test_true_string(self):
        """Test 'true' switches the flag on."""
        assert env_flag("FLAG") is True

    def test_off_synonyms(self):
        """Test the accepted off values, including case and padding."""
        for raw in ("0", "no", "off", "FALSE", "  false  ", "Off"):
            with patch.dict("os.environ", {"FLAG": raw}, clear=True):
                assert env_flag("FLAG") is False, raw

    def test_other_values_are_on(self):
        """Test anything unrecognised counts as enabled."""
        for raw in ("1", "yes", "enabled", "anything"):
            with patch.dict("os.environ", {"FLAG": raw}, clear=True):
                assert env_flag("FLAG") is True, raw
