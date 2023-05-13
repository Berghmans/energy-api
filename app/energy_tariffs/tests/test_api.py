"""Test module for API classes"""
from __future__ import annotations
from unittest import TestCase
from datetime import datetime
import json
import os

from moto import mock_dynamodb

from api import Api
from api.result import ApiResult
from dao import IndexingSetting, IndexingSettingOrigin, IndexingSettingTimeframe
from lambda_api import handler
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestApi(TestCase):
    """Test class for Api"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.base_path = "/v1"
        IndexingSetting(
            "index1",
            1.1,
            IndexingSettingTimeframe.MONTHLY,
            datetime(2023, 5, 1),
            "src",
            IndexingSettingOrigin.ORIGINAL,
        ).save(self.db_table)
        self.valid_request = {
            "path": f"{self.base_path}/indexingsetting",
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
        self.invalid_request = {"path": "/nonexisting", "body": ""}

    def test_handler(self):
        """Test the lambda handler"""
        os.environ["TABLE_NAME"] = self.db_table.name
        os.environ["API_BASE_PATH"] = self.base_path
        result = handler(self.valid_request, {})
        self.assertEqual(200, result["statusCode"])

    def test_existing_method(self):
        """Test an existing API method"""
        api = Api(self.base_path, None)
        method = api.parse(self.valid_request)
        self.assertIsNotNone(method)

    def test_non_existing_method(self):
        """Test an non-existing API method"""
        api = Api(self.base_path, None)
        method = api.parse(self.invalid_request)
        self.assertIsNone(method)

    def test_results(self):
        """Test ApiResult results"""
        good = ApiResult(200, {"result": "good"})
        bad = ApiResult(400, {"result": "bad"})

        self.assertEqual({"statusCode": 200, "body": '{"result": "good"}'}, good.to_api())
        self.assertEqual({"statusCode": 400, "body": '{"result": "bad"}'}, bad.to_api())
