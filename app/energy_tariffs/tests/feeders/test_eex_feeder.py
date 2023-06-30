"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, call
from pathlib import Path
from datetime import date, datetime
import os

import requests_mock
from moto import mock_dynamodb
from pytz import utc

from feeders.eex import EEXIndexingSetting, EEX_URL
from dao.indexingsetting import IndexingSettingOrigin, IndexingSettingTimeframe, IndexingSettingDocumentation
from lambda_feeder import eex_handler as handler
from tests.creators import create_dynamodb_table


def mock_url(mock, index: str, start: date, end: date, file_name: str):
    """Mock the URL to return some text that is stored in given file name"""
    url = (
        EEX_URL + f"?priceSymbol=%22%23E.{index}%22&chartstartdate={start.year}%2F{str(start.month).zfill(2)}%2F{str(start.day).zfill(2)}&"
        f"chartstopdate={end.year}%2F{str(end.month).zfill(2)}%2F{str(end.day).zfill(2)}&"
        f"dailybarinterval=Days&aggregatepriceselection=First"
    )
    with (Path(__file__).parent / "data" / file_name).open(mode="r", encoding="utf-8") as file_handle:
        html_text = file_handle.read()
    mock.get(url, text=html_text)


@requests_mock.Mocker()
class TestEEXIndexingSetting(TestCase):
    """Test class for EEXIndexingSetting"""

    def test_get_ztp_values(self, mock):
        """Test the get_ztp_values method"""
        start = date(2023, 4, 1)
        end = date.today()
        mock_url(mock, "ZTP_GTND", start, end, "eex_ztp_gtnd.json")
        mock_url(mock, "ZTP_GTWE", start, end, "eex_ztp_gtwe.json")
        indexes = EEXIndexingSetting.get_ztp_values(start)
        self.assertEqual(32, len(indexes))
        start = date(2023, 5, 1)
        mock_url(mock, "ZTP_GTND", start, end, "eex_ztp_gtnd.json")
        mock_url(mock, "ZTP_GTWE", start, end, "eex_ztp_gtwe.json")
        indexes = EEXIndexingSetting.get_ztp_values(start)
        self.assertEqual(10, len(indexes))


@mock_dynamodb
class TestLambdaHandlerEngie(TestCase):
    """Test class for lambda engie feeder handler"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        now = datetime.now(utc)
        self.gas_indexes = [
            EEXIndexingSetting(
                "index1",
                1.1,
                IndexingSettingTimeframe.DAILY,
                now,
                "src",
                IndexingSettingOrigin.ORIGINAL,
            )
        ]

    def test_handler(self):
        """Test the lambda handler"""
        # Path these methods so they return a fixed result, as the lambda handler is "moving"
        # and otherwise we would have no consistent results the coming months
        with patch("feeders.eex.EEXIndexingSetting.get_ztp_values", return_value=self.gas_indexes), patch(
            "feeders.eex.EEXIndexingSetting.get_zee_values", return_value=[]
        ):
            os.environ["TABLE_NAME"] = self.db_table.name
            self.assertEqual(0, len(self.db_table.scan().get("Items", [])))
            handler({}, {})
            self.assertEqual(2, len(self.db_table.scan().get("Items", [])))
            self.assertEqual(1, len(IndexingSettingDocumentation.query(self.db_table)))

        with patch("feeders.eex.EEXIndexingSetting.get_ztp_values", return_value=self.gas_indexes) as mock:
            handler({"start": "2023/04/01", "end": "2023/04/30"}, {})
            self.assertEqual([call(date_filter=date(2023, 4, 1), end=date(2023, 4, 30))], mock.mock_calls)
