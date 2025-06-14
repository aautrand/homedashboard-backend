import logging


class IgnoreIcalFilter(logging.Filter):
    def filter(self, record):
        return (
            "Ical data was modified to avoid compatibility issues"
            not in record.getMessage()
        )
