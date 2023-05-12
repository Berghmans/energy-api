"""Test module for API classes"""
from __future__ import annotations
from dataclasses import asdict
from unittest import TestCase
from datetime import datetime

from moto import mock_dynamodb

from api import IndexingSettingApiMethod, EndPriceApiMethod
from dao import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestIndexingSettingApiMethod(TestCase):
    """Test class for IndexingSettingApiMethod"""

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
        self.assertIsNone(IndexingSettingApiMethod.from_body(None, {}))

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertIsNotNone(
            IndexingSettingApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                    "YEAR": 2023,
                    "MONTH": 5,
                },
            )
        )

    def test_process(self):
        """Test the process method"""
        method = IndexingSettingApiMethod(
            db_table=self.db_table,
            index_name=self.index_name,
            index_source=self.index_source,
            index_year=self.index_datetime.year,
            index_month=self.index_datetime.month,
        )
        result = method.process()
        self.assertEqual(200, result.status_code)
        self.assertEqual(asdict(self.index_obj), result.body)

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        method = IndexingSettingApiMethod(
            db_table=self.db_table,
            index_name="otherindex",
            index_source=self.index_source,
            index_year=self.index_datetime.year,
            index_month=self.index_datetime.month,
        )
        result = method.process()
        self.assertEqual(400, result.status_code)
        self.assertEqual({}, result.body)


@mock_dynamodb
class TestEndPriceApiMethod(TestCase):
    """Test class for EndPriceApiMethod"""

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
        self.assertIsNone(EndPriceApiMethod.from_body(None, {}))

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertIsNotNone(
            EndPriceApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                    "YEAR": 2023,
                    "MONTH": 5,
                    "INTERCEPT": 1.0,
                    "SLOPE": 1.0,
                    "TAXES": 1.0,
                },
            )
        )

    def test_process(self):
        """Test the process method"""
        slope = 1.0
        intercept = 1.0
        taxes = 1.5
        method = EndPriceApiMethod(
            db_table=self.db_table,
            index_name=self.index_name,
            index_source=self.index_source,
            index_year=self.index_datetime.year,
            index_month=self.index_datetime.month,
            intercept=intercept,
            slope=slope,
            taxes=taxes,
        )
        result = method.process()
        self.assertEqual(200, result.status_code)
        self.assertEqual({"end_price": ((self.index_value * slope) + intercept) * taxes}, result.body)

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        method = EndPriceApiMethod(
            db_table=self.db_table,
            index_name="otherindex",
            index_source=self.index_source,
            index_year=self.index_datetime.year,
            index_month=self.index_datetime.month,
            intercept=1.0,
            slope=1.0,
            taxes=1.5,
        )
        result = method.process()
        self.assertEqual(400, result.status_code)
        self.assertEqual({}, result.body)
