"""Module that represents the API functionality"""
from __future__ import annotations
from dataclasses import dataclass
import json
import logging

from api.method import ApiMethod
from api.methods import IndexingSettingApiMethod, IndexingSettingsApiMethod, EndPriceApiMethod, EndPricesApiMethod, ListApiMethod


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Api:
    """Class for answering incoming API GW methods"""

    base_path: str
    db_table: object  # Unfortunately not easy typing for boto3

    def parse(self, event: dict) -> ApiMethod:
        """Parse the incoming event through lambda from API Gateway"""

        def has_value(data: dict, key: str, value: str):
            """Check if the data has the key and given value"""
            return key in data and data[key] == value

        if has_value(event, "path", f"{self.base_path}/indexingsetting") and has_value(event, "httpMethod", "POST"):
            return IndexingSettingApiMethod.from_body(self.db_table, json.loads(event.get("body", r"{}")))
        if has_value(event, "path", f"{self.base_path}/indexingsettings") and has_value(event, "httpMethod", "POST"):
            return IndexingSettingsApiMethod.from_body(self.db_table, json.loads(event.get("body", r"{}")))
        if has_value(event, "path", f"{self.base_path}/endprice") and has_value(event, "httpMethod", "POST"):
            return EndPriceApiMethod.from_body(self.db_table, json.loads(event.get("body", r"{}")))
        if has_value(event, "path", f"{self.base_path}/endprices") and has_value(event, "httpMethod", "POST"):
            return EndPricesApiMethod.from_body(self.db_table, json.loads(event.get("body", r"{}")))
        if has_value(event, "path", f"{self.base_path}/list") and has_value(event, "httpMethod", "GET"):
            return ListApiMethod.from_body(self.db_table, {})

        logger.warning("Unable to parse event")
        return None
