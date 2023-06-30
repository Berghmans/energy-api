"""Test module for API classes"""
from __future__ import annotations
from datetime import datetime

from moto import mock_dynamodb
from pytz import utc

from api.methods.end_prices import EndPricesApiMethod
from api.methods.end_price import EndPriceApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from dao.indexingsetting import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestEndPricesApiMethod(TestCaseApiMethod):
    """Test class for EndPricesApiMethod"""

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
        self.assertBodyInvalid(EndPricesApiMethod, {})
        self.assertBodyInvalid(EndPricesApiMethod, {"q1": {}})

    def test_from_body_valid(self):
        """Test the from_body method"""
        request = {
            "INDEX": "index1",
            "SOURCE": "src",
            "DATE": "2023-05-01 00:00",
            "INTERCEPT": 1.0,
            "SLOPE": 1.0,
            "TAXES": 1.0,
        }
        self.assertBodyValid(
            EndPricesApiMethod,
            {
                "q1": request,
                "q2": request,
            },
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
            name=self.index_name,
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
        )
        bare_method_result = bare_method.process()
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
        expected = {**bare_method_result.body, "end_price": ((self.index_value * slope) + intercept) * taxes}
        self.assertProcess(method, 200, {"q1": expected, "q2": expected})

    def test_process_not_existing(self):
        """Test the process method for a not existing EndPrice"""
        bare_method = IndexingSettingApiMethod(
            db_table=self.db_table,
            name="otherindex",
            source=self.index_source,
            date=datetime(year=self.index_datetime.year, month=self.index_datetime.month, day=1),
            timeframe=IndexingSettingTimeframe.MONTHLY,
            origin=IndexingSettingOrigin.ORIGINAL,
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
        self.assertProcess(method, 400, {"error": "No result found for one of the requested indices"})
