"""Test module for API classes"""
from __future__ import annotations

from moto import mock_dynamodb

from api.methods.list import ListApiMethod
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestListApiMethod(TestCaseApiMethod):
    """Test class for ListApiMethod"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.load_db(self.db_table, "db_indexingsettings.json")

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertBodyValid(ListApiMethod, {})
        self.assertBodyValid(
            ListApiMethod,
            {
                "Anything": "can",
                "be": "here",
            },
        )

    def test_process(self):
        """Test the process method"""
        method = ListApiMethod(db_table=self.db_table)
        expected = [
            {
                "name": "index2",
                "timeframe": "HOURLY",
                "source": "src",
                "origin": "ORIGINAL",
            },
            {
                "name": "index1",
                "timeframe": "MONTHLY",
                "source": "src",
                "origin": "ORIGINAL",
            },
            {
                "name": "index3",
                "timeframe": "MONTHLY",
                "source": "src",
                "origin": "DERIVED",
            },
        ]
        self.assertProcess(method, 200, expected)
