"""Test module for API classes"""
from __future__ import annotations
from unittest import TestCase
from datetime import datetime
import json
import os

from moto import mock_dynamodb
from pytz import utc

from api import Api
from api.method import ApiMethod
from api.result import ApiResult
from dao.indexingsetting import IndexingSetting, IndexingSettingOrigin, IndexingSettingTimeframe
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
            datetime(2023, 4, 1, tzinfo=utc),
            "src",
            IndexingSettingOrigin.ORIGINAL,
        ).save(self.db_table)
        self.valid_body = {
            "INDEX": "index1",
            "SOURCE": "src",
            "DATE": "2023-05-01 00:00",
        }
        self.valid_request = {
            "path": f"{self.base_path}/indexingsetting",
            "httpMethod": "POST",
            "body": json.dumps(self.valid_body),
        }
        self.invalid_request = {"path": "/nonexisting", "body": ""}

    def test_handler(self):
        """Test the lambda handler"""
        os.environ["TABLE_NAME"] = self.db_table.name
        os.environ["API_BASE_PATH"] = self.base_path
        result = handler(self.valid_request, {})
        self.assertEqual(200, result["statusCode"])
        result = handler({**self.valid_request, "path": f"{self.base_path}/notexisting"}, {})
        self.assertEqual(400, result["statusCode"])

    def test_not_implemented_method(self):
        """Test an existing API method"""
        method = ApiMethod()
        self.assertRaises(NotImplementedError, method.process)

    def test_existing_method(self):
        """Test an existing API method"""
        api = Api(self.base_path, None)
        # /indexsetting
        self.assertIsNotNone(api.parse(self.valid_request))
        # /indexsettings
        self.assertIsNotNone(api.parse({**self.valid_request, "path": f"{self.base_path}/indexingsettings", "body": json.dumps({"q1": self.valid_body})}))
        # /endprice
        body = {
            **self.valid_body,
            "INTERCEPT": 1.0,
            "SLOPE": 1.0,
            "TAXES": 1.0,
        }
        self.assertIsNotNone(api.parse({**self.valid_request, "path": f"{self.base_path}/endprice", "body": json.dumps(body)}))
        # /endprices
        self.assertIsNotNone(api.parse({**self.valid_request, "path": f"{self.base_path}/endprices", "body": json.dumps({"q1": body})}))
        # /list
        self.assertIsNotNone(api.parse({"httpMethod": "GET", "path": f"{self.base_path}/list", "body": json.dumps({})}))

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
