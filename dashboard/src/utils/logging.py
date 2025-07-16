import logging
from logging.config import dictConfig


class IgnoreIcalFilter(logging.Filter):
    def filter(self, record):
        return (
            "Ical data was modified to avoid compatibility issues"
            not in record.getMessage()
        )


def setup_logging():
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "detailed": {
                    "format": (
                        "[%(asctime)s] %(levelname)s "
                        "in %(name)s (%(filename)s:%(lineno)d): %(message)s"
                    ),
                },
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "formatter": "detailed",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["wsgi"],
            },
        }
    )
    logging.getLogger().addFilter(IgnoreIcalFilter())
