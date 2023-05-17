"""Test module for API classes"""
from __future__ import annotations
from dataclasses import asdict
from unittest import TestCase
from datetime import datetime

from moto import mock_dynamodb
from pytz import utc

from api.methods.indexing_setting import IndexingSettingApiMethod
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
        self.index_datetime = datetime(2023, 5, 1, 0, 0, 0, tzinfo=utc)
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
        self.assertIsNone(
            IndexingSettingApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                    "DATE": "somedate",
                },
            )
        )
        self.assertIsNone(
            IndexingSettingApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                    "TIMEFRAME": "badvalue",
                },
            )
        )
        self.assertIsNone(
            IndexingSettingApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                    "ORIGIN": "badvalue",
                },
            )
        )

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertIsNotNone(
            IndexingSettingApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                    "DATE": "2023-05-01 00:00",
                },
            )
        )
        self.assertIsNotNone(
            IndexingSettingApiMethod.from_body(
                None,
                {
                    "INDEX": "index1",
                    "SOURCE": "src",
                },
            )
        )

    def test_process(self):
        """Test the process method"""
        method = IndexingSettingApiMethod(
            db_table=self.db_table,
            name=self.index_name,
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
        )
        result = method.process()
        self.assertEqual(200, result.status_code)
        expected = {**asdict(self.index_obj), "timeframe": self.index_timeframe.name, "origin": self.index_origin.name}
        self.assertEqual(expected, result.body)

    def test_from_body_monthly(self):
        """Test the from_body method"""
        method = IndexingSettingApiMethod.from_body(
            self.db_table,
            {"INDEX": self.index_name, "SOURCE": self.index_source, "DATE": "2023-06-01 10:00", "TIMEFRAME": "MONTHLY", "ORIGIN": "ORIGINAL"},
        )
        self.assertIsNotNone(method)
        result = method.process()
        self.assertEqual(200, result.status_code)
        expected = {
            "name": self.index_name,
            "source": self.index_source,
            "date": datetime(2023, 5, 1, 0, 0, tzinfo=utc),  # We indeed expect last month's results
            "value": self.index_value,
            "timeframe": "MONTHLY",
            "origin": "ORIGINAL",
        }
        self.assertEqual(expected, result.body)

    def test_from_body_hourly(self):
        """Test the from_body method"""
        IndexingSetting(
            self.index_name,
            self.index_value,
            IndexingSettingTimeframe.HOURLY,
            datetime(year=2023, month=5, day=1, hour=10, tzinfo=utc),
            self.index_source,
            IndexingSettingOrigin.DERIVED,
        ).save(self.db_table)
        method = IndexingSettingApiMethod.from_body(
            self.db_table,
            {"INDEX": self.index_name, "SOURCE": self.index_source, "DATE": "2023-05-01 10:00", "TIMEFRAME": "HOURLY", "ORIGIN": "DERIVED"},
        )
        self.assertIsNotNone(method)
        result = method.process()
        self.assertEqual(200, result.status_code)
        expected = {
            "name": self.index_name,
            "source": self.index_source,
            "date": datetime(2023, 5, 1, 10, 0, tzinfo=utc),
            "value": self.index_value,
            "timeframe": "HOURLY",
            "origin": "DERIVED",
        }
        self.assertEqual(expected, result.body)

    def test_from_body_daily(self):
        """Test the from_body method"""
        IndexingSetting(
            self.index_name,
            self.index_value,
            IndexingSettingTimeframe.DAILY,
            datetime(year=2023, month=5, day=1, tzinfo=utc),
            self.index_source,
            IndexingSettingOrigin.DERIVED,
        ).save(self.db_table)
        method = IndexingSettingApiMethod.from_body(
            self.db_table,
            {"INDEX": self.index_name, "SOURCE": self.index_source, "DATE": "2023-05-01 10:00", "TIMEFRAME": "DAILY", "ORIGIN": "DERIVED"},
        )
        self.assertIsNone(method)

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        method = IndexingSettingApiMethod(
            db_table=self.db_table,
            name="otherindex",
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
        )
        result = method.process()
        self.assertEqual(400, result.status_code)
        self.assertEqual({}, result.body)
