"""Test module for API classes"""
from __future__ import annotations
from unittest import TestCase
import json

from moto import mock_dynamodb

from api import Api


@mock_dynamodb
class TestApi(TestCase):
    """Test class for Api"""

    def test_existing_method(self):
        """Test an existing API method"""
        api = Api(None)
        method = api.parse(
            {
                "resource": "/indexingsetting",
                "body": json.dumps(
                    {
                        "INDEX": "index1",
                        "SOURCE": "src",
                        "YEAR": 2023,
                        "MONTH": 5,
                    }
                ),
            }
        )
        self.assertIsNotNone(method)

    def test_non_existing_method(self):
        """Test an non-existing API method"""
        api = Api(None)
        method = api.parse({"resource": "/nonexisting", "body": ""})
        self.assertIsNone(method)
