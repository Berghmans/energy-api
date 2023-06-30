"""Module for representing a result to API Gateway"""
from dataclasses import dataclass, field
import json


@dataclass
class ApiResult:
    """The result of the API method"""

    status_code: int
    body: dict = field(default_factory=lambda: {})

    def to_api(self) -> dict:
        """Transform to output for the API"""
        return {"statusCode": self.status_code, "body": json.dumps(self.body, default=str)}


class Success(ApiResult):
    """The HTTP 200 result"""

    def __init__(self, result: dict):
        super().__init__(200, result)


class BadRequest(ApiResult):
    """The HTTP 400 result"""

    def __init__(self, error_msg):
        super().__init__(400, {"error": error_msg})
