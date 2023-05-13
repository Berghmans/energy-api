"""Module for an interface for API Methods"""
from api.result import ApiResult


class ApiMethod:
    """Class for processing a method"""

    def process(self) -> ApiResult:
        """Process the method"""
        raise NotImplementedError("This method is not implemented")
