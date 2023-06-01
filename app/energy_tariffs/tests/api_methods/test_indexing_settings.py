"""Test module for API classes"""
from __future__ import annotations
from datetime import datetime

from moto import mock_dynamodb
from pytz import utc

from api.methods.indexing_settings import IndexingSettingsApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from dao import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestIndexingSettingsApiMethod(TestCaseApiMethod):
    """Test class for IndexingSettingsApiMethod"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.load_db(self.db_table, "db_indexingsettings.json")
        self.index_name = "index1"
        self.index_timeframe = IndexingSettingTimeframe.MONTHLY
        self.index_datetime = datetime(2023, 5, 1, 0, 0, 0, tzinfo=utc)
        self.index_source = "src"
        self.index_origin = IndexingSettingOrigin.ORIGINAL
        self.index_value = 1.1
        self.assertIsNotNone(IndexingSetting.load(self.db_table, self.index_source, self.index_name, self.index_timeframe, self.index_datetime))

    def test_from_body_invalid(self):
        """Test the from_body method with invalid input"""
        self.assertBodyInvalid(IndexingSettingsApiMethod, {})
        self.assertBodyInvalid(IndexingSettingsApiMethod, {"q1": {}})

    def test_from_body_valid(self):
        """Test the from_body method"""
        request = {
            "INDEX": "index1",
            "SOURCE": "src",
            "DATE": "2023-05-01 00:00",
        }
        self.assertBodyValid(
            IndexingSettingsApiMethod,
            {
                "q1": request,
                "q2": request,
            },
        )
        self.assertBodyValid(
            IndexingSettingsApiMethod,
            {
                "q1": request,
                "q2": request,
                "q3": request,
                "q4": request,
                "q5": request,
                "q6": request,
            },
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
        expected = {
            "name": self.index_name,
            "value": self.index_value,
            "date": self.index_datetime,
            "source": self.index_source,
            "timeframe": self.index_timeframe.name,
            "origin": self.index_origin.name,
        }
        self.assertProcess(method, 200, {"q1": expected, "q2": expected})

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
        self.assertProcess(method, 400, {})
