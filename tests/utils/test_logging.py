import logging
from unittest.mock import patch

from dashboard.src.utils.logging import IgnoreIcalFilter, setup_logging


class TestIgnoreIcalFilter:

    def test_allows_normal_message(self):
        f = IgnoreIcalFilter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "Normal log message", (), None
        )
        assert f.filter(record) is True

    def test_blocks_ical_compatibility_message(self):
        f = IgnoreIcalFilter()
        record = logging.LogRecord(
            "test",
            logging.WARNING,
            "",
            0,
            "Ical data was modified to avoid compatibility issues",
            (),
            None,
        )
        assert f.filter(record) is False

    def test_blocks_message_containing_ical_text(self):
        f = IgnoreIcalFilter()
        record = logging.LogRecord(
            "test",
            logging.INFO,
            "",
            0,
            "Some prefix: Ical data was modified to avoid compatibility issues more text",
            (),
            None,
        )
        assert f.filter(record) is False


class TestSetupLogging:

    def test_configures_logging(self):
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO
        # Should have at least one handler
        assert len(root.handlers) > 0
        # Should have the IgnoreIcalFilter
        has_filter = any(isinstance(f, IgnoreIcalFilter) for f in root.filters)
        assert has_filter
