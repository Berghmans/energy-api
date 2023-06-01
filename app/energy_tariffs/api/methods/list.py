"""Module for the end price method"""
from dataclasses import dataclass, asdict
import logging
import json

from api.method import ApiMethod
from api.result import ApiResult
from dao import IndexingSettingDocumentation


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class ListApiMethod(ApiMethod):
    """Method for /list"""

    db_table: object  # Unfortunately not easy typing for boto3

    def process(self) -> ApiResult:
        docs = IndexingSettingDocumentation.query(self.db_table)
        docs_list = [{**asdict(doc), "timeframe": doc.timeframe.name, "origin": doc.origin.name} for doc in docs]
        return ApiResult(200, docs_list)

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}, although body is not needed")
        return cls(db_table)
