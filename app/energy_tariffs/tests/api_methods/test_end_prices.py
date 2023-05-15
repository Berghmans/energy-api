"""Test module for API classes"""
from __future__ import annotations
from unittest import TestCase
from datetime import datetime

from moto import mock_dynamodb

from api.methods.end_prices import EndPricesApiMethod
from api.methods.end_price import EndPriceApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from dao import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestEndPricesApiMethod(TestCase):
    """Test class for EndPricesApiMethod"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.index_name = "index1"
        self.index_timeframe = IndexingSettingTimeframe.MONTHLY
        self.index_datetime = datetime(2023, 5, 1, 0, 0, 0)
        self.index_datetime_str = "2023-05-01 05:00:00"
        self.index_source = "src"
        self.index_origin = IndexingSettingOrigin.ORIGINAL
        self.index_value = 1.1
        self.index_obj = IndexingSetting(
            self.index_name,
            self.index_value,
            self.index_timeframe,
            self.index_datetime,
            self.index_source,
            self.index_origin,
        )
        self.index_obj.save(self.db_table)
        self.assertIsNotNone(IndexingSetting.load(self.db_table, self.index_source, self.index_name, self.index_timeframe, self.index_datetime))

    def test_from_body_invalid(self):
        """Test the from_body method with invalid input"""
        self.assertIsNone(EndPricesApiMethod.from_body(None, {"q1": {}}))

    def test_from_body_valid(self):
        """Test the from_body method"""
        request = {
            "INDEX": "index1",
            "SOURCE": "src",
            "YEAR": 2023,
            "MONTH": 5,
            "INTERCEPT": 1.0,
            "SLOPE": 1.0,
            "TAXES": 1.0,
        }
        self.assertIsNotNone(
            EndPricesApiMethod.from_body(
                None,
                {
                    "q1": request,
                    "q2": request,
                },
            )
        )
        method = EndPricesApiMethod.from_body(
            None,
            {
                "q1": request,
                "q2": request,
                "q3": request,
                "q4": request,
                "q5": request,
                "q6": request,
            },
        )
        self.assertEqual(5, len(method.indexes))

    def test_process(self):
        """Test the process method"""
        bare_method = IndexingSettingApiMethod(
            db_table=self.db_table,
            index_name=self.index_name,
            index_source=self.index_source,
            index_year=self.index_datetime.year,
            index_month=self.index_datetime.month,
        )
        slope = 1.0
        intercept = 1.0
        taxes = 1.5
        request = EndPriceApiMethod(
            index=bare_method,
            intercept=intercept,
            slope=slope,
            taxes=taxes,
        )
        method = EndPricesApiMethod(
            indexes={
                "q1": request,
                "q2": request,
            }
        )
        result = method.process()
        self.assertEqual(200, result.status_code)
        expected = {"end_price": ((self.index_value * slope) + intercept) * taxes}
        self.assertEqual({"q1": expected, "q2": expected}, result.body)

    def test_process_not_existing(self):
        """Test the process method for a not existing EndPrice"""
        bare_method = IndexingSettingApiMethod(
            db_table=self.db_table,
            index_name="otherindex",
            index_source=self.index_source,
            index_year=self.index_datetime.year,
            index_month=self.index_datetime.month,
        )
        method = EndPricesApiMethod(
            indexes={
                "q1": EndPriceApiMethod(
                    index=bare_method,
                    intercept=1.0,
                    slope=1.0,
                    taxes=1.5,
                ),
                "q2": EndPriceApiMethod(
                    index=bare_method,
                    intercept=1.0,
                    slope=1.0,
                    taxes=1.5,
                ),
            }
        )
        result = method.process()
        self.assertEqual(400, result.status_code)
        self.assertEqual({}, result.body)
