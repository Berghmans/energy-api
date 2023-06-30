"""Module for the end prices method - The same as indexing setting but for multiple at once"""
from dataclasses import dataclass
from itertools import islice
import logging
import json

from api.method import ApiMethod
from api.methods.end_price import EndPriceApiMethod
from api.result import ApiResult, Success, BadRequest


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class EndPricesApiMethod(ApiMethod):
    """Method for /endprices"""

    indexes: dict[str, EndPriceApiMethod]

    def process(self) -> ApiResult:
        results = {key: request.process() for key, request in self.indexes.items()}

        if any(result.status_code != 200 for result in results.values()):
            return BadRequest("No result found for one of the requested indices")

        return Success({key: result.body for key, result in results.items()})

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if len(body) == 0:
            return None

        index_requests = {key: EndPriceApiMethod.from_body(db_table, index_request) for key, index_request in body.items()}

        if any(request is None for request in index_requests.values()):
            logger.info("One of the requests was not falid")
            return None

        return cls(indexes=dict(islice(index_requests.items(), 5)))  # Limit to 5 requests for performance reasons
