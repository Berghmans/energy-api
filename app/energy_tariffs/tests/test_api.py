"""Test module for API classes"""
from __future__ import annotations
from unittest import TestCase
import json

from moto import mock_dynamodb

from api import Api
from api.result import ApiResult


@mock_dynamodb
class TestApi(TestCase):
    """Test class for Api"""

    def test_existing_method(self):
        """Test an existing API method"""
        api = Api("", None)
        method = api.parse(
            {
                "path": "/indexingsetting",
                "httpMethod": "POST",
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
        api = Api("", None)
        method = api.parse({"path": "/nonexisting", "body": ""})
        self.assertIsNone(method)

    def test_results(self):
        """Test ApiResult results"""
        good = ApiResult(200, {"result": "good"})
        bad = ApiResult(400, {"result": "bad"})

        self.assertEqual({"statusCode": 200, "body": '{"result": "good"}'}, good.to_api())
        self.assertEqual({"statusCode": 400, "body": '{"result": "bad"}'}, bad.to_api())
