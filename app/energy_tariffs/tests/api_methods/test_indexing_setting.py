"""Test module for API classes"""
from __future__ import annotations
from datetime import datetime

from moto import mock_dynamodb
from pytz import utc

from api.methods.indexing_setting import IndexingSettingApiMethod
from dao.indexingsetting import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestIndexingSettingApiMethod(TestCaseApiMethod):
    """Test class for IndexingSettingApiMethod"""

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
        self.assertBodyInvalid(IndexingSettingApiMethod, {})
        self.assertBodyInvalid(
            IndexingSettingApiMethod,
            {
                "INDEX": "index1",
                "SOURCE": "src",
                "DATE": "somedate",
            },
        )
        self.assertBodyInvalid(
            IndexingSettingApiMethod,
            {
                "INDEX": "index1",
                "SOURCE": "src",
                "TIMEFRAME": "badvalue",
            },
        )
        self.assertBodyInvalid(
            IndexingSettingApiMethod,
            {
                "INDEX": "index1",
                "SOURCE": "src",
                "ORIGIN": "badvalue",
            },
        )

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertBodyValid(
            IndexingSettingApiMethod,
            {
                "INDEX": "index1",
                "SOURCE": "src",
                "DATE": "2023-05-01 00:00",
            },
        )
        self.assertBodyValid(
            IndexingSettingApiMethod,
            {
                "INDEX": "index1",
                "SOURCE": "src",
            },
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
        expected = {
            "name": self.index_name,
            "value": self.index_value,
            "date": self.index_datetime,
            "source": self.index_source,
            "timeframe": self.index_timeframe.name,
            "origin": self.index_origin.name,
        }
        self.assertProcess(method, 200, expected)

    def test_from_body_monthly(self):
        """Test the from_body method"""
        method = IndexingSettingApiMethod.from_body(
            self.db_table,
            {"INDEX": self.index_name, "SOURCE": self.index_source, "DATE": "2023-06-01 10:00", "TIMEFRAME": "MONTHLY", "ORIGIN": "ORIGINAL"},
        )
        expected = {
            "name": self.index_name,
            "source": self.index_source,
            "date": datetime(2023, 5, 1, 0, 0, tzinfo=utc),  # We indeed expect last month's results
            "value": self.index_value,
            "timeframe": "MONTHLY",
            "origin": "ORIGINAL",
        }
        self.assertProcess(method, 200, expected)

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
        expected = {
            "name": self.index_name,
            "source": self.index_source,
            "date": datetime(2023, 5, 1, 10, 0, tzinfo=utc),
            "value": self.index_value,
            "timeframe": "HOURLY",
            "origin": "DERIVED",
        }
        self.assertProcess(method, 200, expected)

    def test_from_body_daily(self):
        """Test the from_body method"""
        # DAILY is not implemented yet so we expect failing parsing the body
        self.assertBodyInvalid(
            IndexingSettingApiMethod,
            {"INDEX": self.index_name, "SOURCE": self.index_source, "DATE": "2023-05-01 10:00", "TIMEFRAME": "DAILY", "ORIGIN": "DERIVED"},
        )
        IndexingSetting(
            self.index_name,
            self.index_value,
            IndexingSettingTimeframe.DAILY,
            datetime(year=2023, month=5, day=1, tzinfo=utc),
            self.index_source,
            IndexingSettingOrigin.DERIVED,
        ).save(self.db_table)
        # Even after we save information in the database
        self.assertBodyInvalid(
            IndexingSettingApiMethod,
            {"INDEX": self.index_name, "SOURCE": self.index_source, "DATE": "2023-05-01 10:00", "TIMEFRAME": "DAILY", "ORIGIN": "DERIVED"},
        )

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
        self.assertProcess(method, 400, {"error": "No result found for requested index"})
