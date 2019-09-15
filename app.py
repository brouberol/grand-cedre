import re

from grand_cedre.web import app

from datetime import datetime
from pythonjsonlogger.jsonlogger import JsonFormatter


FIELD_PATTERN = re.compile(r"\{(\w+)\}\w")


class GunicornJsonFormatter(JsonFormatter):

    header_whitelist = []

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        log_record["logger"] = record.name
        log_record["level"] = record.levelname

        if record.args:
            log_record["request"] = {}
            log_record.pop("message", None)
            log_record["request"]["timestamp"] = datetime.strptime(
                record.args["t"].strip("[]"), "%d/%b/%Y:%H:%M:%S +%f"
            )
            for fieldname, value in record.args.items():
                m = re.match(FIELD_PATTERN, fieldname)
                if m:
                    log_record["request"][m.group(1)] = value

            for fieldname in log_record["request"].copy():
                if fieldname.startswith("http_"):
                    plain_fieldname = fieldname.replace("http_", "")
                    if plain_fieldname in self.header_whitelist:
                        log_record["request"][fieldname] = log_record["request"].pop(
                            plain_fieldname
                        )
                    else:
                        log_record["request"].pop(fieldname, None)
                        log_record["request"].pop(plain_fieldname, None)
