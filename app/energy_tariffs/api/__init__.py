"""Module that represents the API functionality"""
from __future__ import annotations
from dataclasses import dataclass
import json
import logging

from api.method import ApiMethod
from api.methods import (
    IndexingSettingApiMethod,
    IndexingSettingsApiMethod,
    EndPriceApiMethod,
    EndPricesApiMethod,
    ListApiMethod,
    GridCostApiMethod,
    ExciseApiMethod,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

METHOD_MAP = {
    ("indexingsetting", "POST"): IndexingSettingApiMethod,
    ("indexingsettings", "POST"): IndexingSettingsApiMethod,
    ("endprice", "POST"): EndPriceApiMethod,
    ("endprices", "POST"): EndPricesApiMethod,
    ("list", "GET"): ListApiMethod,
    ("gridcost", "POST"): GridCostApiMethod,
    ("excise", "POST"): ExciseApiMethod,
}


@dataclass
class Api:
    """Class for answering incoming API GW methods"""

    base_path: str
    db_table: object  # Unfortunately not easy typing for boto3

    def parse(self, event: dict) -> ApiMethod:
        """Parse the incoming event through lambda from API Gateway"""
        path = str(event.get("path", "")).removeprefix(self.base_path).strip("/")
        method = str(event.get("httpMethod", ""))
        call_method = METHOD_MAP.get((path, method))
        if call_method is not None:
            return call_method.from_body(self.db_table, json.loads(event.get("body", r"{}")))

        logger.warning("Unable to parse event")
        return None
