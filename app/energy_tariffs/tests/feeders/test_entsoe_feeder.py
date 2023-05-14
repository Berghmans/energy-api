"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, call
from pathlib import Path
from datetime import date
from statistics import mean
import os

import pandas
from moto import mock_dynamodb

from feeders.entsoe import EntsoeIndexingSetting
from lambda_entsoe import handler
from tests.creators import create_dynamodb_table


def read_entsoe_values(file_name: str) -> pandas.Series:
    """Read the ENSTO-E values from a file"""
    file_path = Path(__file__).parent / "data" / file_name
    df = pandas.read_csv(file_path, index_col=0, header=0)
    df.index = pandas.to_datetime(df.index)
    return df.squeeze("columns")


class TestEEXIndexingSetting(TestCase):
    """Test class for EEXIndexingSetting"""

    def test_get_be_values(self):
        """Test the get_ztp_values method"""
        series = read_entsoe_values("entsoe_be.csv")
        with patch("feeders.entsoe.EntsoePandasClient.query_day_ahead_prices", return_value=series):
            start = date(2023, 4, 1)
            end = date(2023, 5, 1)
            indexes = EntsoeIndexingSetting.get_be_values(api_key="key", date_filter=start, end=end)
            self.assertEqual(721, len(indexes))
            self.assertEqual(mean(series.to_dict().values()), mean(index.value for index in indexes))


@mock_dynamodb
class TestLambdaHandlerEntsoe(TestCase):
    """Test class for lambda entsoe feeder handler"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()

    def test_handler(self):
        """Test the lambda handler"""
        # Path these methods so they return a fixed result, as the lambda handler is "moving"
        # and otherwise we would have no consistent results the coming months
        series = read_entsoe_values("entsoe_be.csv")
        with patch("feeders.entsoe.EntsoePandasClient.query_day_ahead_prices", return_value=series):
            os.environ["TABLE_NAME"] = self.db_table.name
            os.environ["ENTSOE_KEY"] = "fakekey"
            self.assertEqual(0, len(self.db_table.scan().get("Items", [])))
            handler({}, {})
            self.assertEqual(721, len(self.db_table.scan().get("Items", [])))

        with patch("feeders.entsoe.EntsoeIndexingSetting.query", return_value=[]) as mock:
            handler({"start": "2023/04/01", "end": "2023/04/15"}, {})
            self.assertEqual([call(api_key="fakekey", country_code="BE", start=date(2023, 4, 1), end=date(2023, 4, 16))], mock.mock_calls)
