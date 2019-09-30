from . import app
import logging

from pythonjsonlogger.jsonlogger import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        if message_dict.get("etag"):
            log_record["event"] = message_dict
            message_dict = {}
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record["logger"] = record.name
        log_record["level"] = record.levelname
        log_record.pop("name")
        log_record.pop("levelname")


logger = app.logger
handler = logging.StreamHandler()
format_str = "%(message)%(levelname)%(name)%(asctime)"
formatter = CustomJsonFormatter(format_str)
handler.setFormatter(formatter)
logger.handlers[0] = handler
logger.propagate = False
