"""Test module for API classes"""
from __future__ import annotations
from dataclasses import asdict
from unittest import TestCase
from datetime import datetime

from moto import mock_dynamodb
from pytz import utc

from api.methods.indexing_settings import IndexingSettingsApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from dao import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestIndexingSettingsApiMethod(TestCase):
    """Test class for IndexingSettingsApiMethod"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.index_name = "index1"
        self.index_timeframe = IndexingSettingTimeframe.MONTHLY
        self.index_datetime = datetime(2023, 5, 1, 0, 0, 0, tzinfo=utc)
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
        self.assertIsNone(IndexingSettingsApiMethod.from_body(None, {"q1": {}}))

    def test_from_body_valid(self):
        """Test the from_body method"""
        request = {
            "INDEX": "index1",
            "SOURCE": "src",
            "DATE": "2023-05-01 00:00",
        }
        self.assertIsNotNone(
            IndexingSettingsApiMethod.from_body(
                None,
                {
                    "q1": request,
                    "q2": request,
                },
            )
        )
        method = IndexingSettingsApiMethod.from_body(
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
        request = IndexingSettingApiMethod(
            db_table=self.db_table,
            name=self.index_name,
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
        )
        method = IndexingSettingsApiMethod(
            indexes={
                "q1": request,
                "q2": request,
            }
        )
        result = method.process()
        self.assertEqual(200, result.status_code)
        expected = {**asdict(self.index_obj), "timeframe": self.index_timeframe.name, "origin": self.index_origin.name}
        self.assertEqual({"q1": expected, "q2": expected}, result.body)

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        method = IndexingSettingsApiMethod(
            indexes={
                "q1": IndexingSettingApiMethod(
                    db_table=self.db_table,
                    name=self.index_name,
                    source=self.index_source,
                    date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
                    timeframe=IndexingSettingTimeframe.MONTHLY,
                    origin=IndexingSettingOrigin.ORIGINAL,
                ),
                "q2": IndexingSettingApiMethod(
                    db_table=self.db_table,
                    name="otherindex",
                    source=self.index_source,
                    date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
                    timeframe=IndexingSettingTimeframe.MONTHLY,
                    origin=IndexingSettingOrigin.ORIGINAL,
                ),
            }
        )
        result = method.process()
        self.assertEqual(400, result.status_code)
        self.assertEqual({}, result.body)
