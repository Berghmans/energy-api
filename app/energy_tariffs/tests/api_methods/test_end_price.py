"""Test module for end price method"""
from __future__ import annotations
from datetime import datetime

from moto import mock_dynamodb
from pytz import utc

from api.methods.end_price import EndPriceApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from dao.indexingsetting import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestEndPriceApiMethod(TestCaseApiMethod):
    """Test class for EndPriceApiMethod"""

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
        self.assertBodyInvalid(EndPriceApiMethod, {})

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertBodyValid(
            EndPriceApiMethod,
            {
                "INDEX": "index1",
                "SOURCE": "src",
                "DATE": "2023-05-01 00:00",
                "INTERCEPT": 1.0,
                "SLOPE": 1.0,
                "TAXES": 1.0,
            },
        )

    def test_process(self):
        """Test the process method"""
        slope = 1.0
        intercept = 1.0
        taxes = 1.5
        bare_method = IndexingSettingApiMethod(
            db_table=self.db_table,
            name=self.index_name,
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
        )
        bare_result = bare_method.process()
        method = EndPriceApiMethod(
            index=bare_method,
            intercept=intercept,
            slope=slope,
            taxes=taxes,
        )
        self.assertProcess(method, 200, {**bare_result.body, "end_price": ((self.index_value * slope) + intercept) * taxes})

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        bare_method = IndexingSettingApiMethod(
            db_table=self.db_table,
            name="otherindex",
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
        )
        method = EndPriceApiMethod(
            index=bare_method,
            intercept=1.0,
            slope=1.0,
            taxes=1.5,
        )
        self.assertProcess(method, 400, {})
