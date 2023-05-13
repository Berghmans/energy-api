"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
from datetime import datetime
import os

import requests_mock
from moto import mock_dynamodb

from engie import EngieIndexingSetting, GAS_URL, ENERGY_URL
from dao import IndexingSettingOrigin, IndexingSettingTimeframe
from lambda_engie import handler
from tests.creators import create_dynamodb_table


def mock_url(mock, url: str, file_name: str):
    """Mock the URL to return some text that is stored in given file name"""
    with (Path(__file__).parent / "data" / file_name).open(mode="r", encoding="utf-8") as file_handle:
        html_text = file_handle.read()
    mock.get(url, text=html_text)


@requests_mock.Mocker()
class TestEngieIndexingSetting(TestCase):
    """Test class for EngieIndexingSetting"""

    def test_from_gas_url(self, mock):
        """Test the from_url method for gas"""
        url = "https://some-fake-url.com/gas"
        mock_url(mock, url, "engie_gas.html")
        indexes = EngieIndexingSetting.from_url(url)
        self.assertEqual(134, len(indexes))
        self.assertTrue(all([index.source == "Engie" for index in indexes]))
        self.assertTrue(all([index.timeframe == IndexingSettingTimeframe.MONTHLY for index in indexes]))
        self.assertTrue(all([index.date.day == 1 for index in indexes]))
        self.assertTrue(all([index.origin == IndexingSettingOrigin.ORIGINAL for index in indexes]))

    def test_from_energy_url(self, mock):
        """Test the from_url method for gas"""
        url = "https://some-fake-url.com/energy"
        mock_url(mock, url, "engie_energy.html")
        indexes = EngieIndexingSetting.from_url(url)
        self.assertEqual(109, len(indexes))
        self.assertTrue(all([index.source == "Engie" for index in indexes]))
        self.assertTrue(all([index.timeframe == IndexingSettingTimeframe.MONTHLY for index in indexes]))
        self.assertTrue(all([index.date.day == 1 for index in indexes]))
        self.assertTrue(all([index.origin == IndexingSettingOrigin.ORIGINAL for index in indexes]))

    def test_get_gas_values(self, mock):
        """Test the get_gas_values method"""
        mock_url(mock, GAS_URL, "engie_gas.html")
        indexes = EngieIndexingSetting.get_gas_values()
        self.assertEqual(134, len(indexes))
        indexes = EngieIndexingSetting.get_gas_values(date_filter=datetime(2023, 4, 1))
        self.assertEqual(8, len(indexes))

    def test_get_energy_values(self, mock):
        """Test the get_energy_values method"""
        mock_url(mock, ENERGY_URL, "engie_energy.html")
        indexes = EngieIndexingSetting.get_energy_values()
        self.assertEqual(109, len(indexes))
        indexes = EngieIndexingSetting.get_energy_values(date_filter=datetime(2023, 4, 1))
        self.assertEqual(7, len(indexes))


@mock_dynamodb
class TestLambdaHandlerEngie(TestCase):
    """Test class for lambda engie feeder handler"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        now = datetime.now()
        self.gas_indexes = [
            EngieIndexingSetting(
                "index1",
                1.1,
                IndexingSettingTimeframe.MONTHLY,
                datetime(now.year, now.month, 1),
                "src",
                IndexingSettingOrigin.ORIGINAL,
            )
        ]
        self.energy_indexes = [
            EngieIndexingSetting(
                "index2",
                1.1,
                IndexingSettingTimeframe.MONTHLY,
                datetime(now.year, now.month, 1),
                "src",
                IndexingSettingOrigin.ORIGINAL,
            )
        ]

    def test_handler(self):
        """Test the lambda handler"""
        # Path these methods so they return a fixed result, as the lambda handler is "moving"
        # and otherwise we would have no consistent results the coming months
        with patch("engie.EngieIndexingSetting.get_gas_values", return_value=self.gas_indexes), patch(
            "engie.EngieIndexingSetting.get_energy_values", return_value=self.energy_indexes
        ):
            os.environ["TABLE_NAME"] = self.db_table.name
            self.assertEqual(0, len(self.db_table.scan().get("Items", [])))
            handler({}, {})
            self.assertEqual(2, len(self.db_table.scan().get("Items", [])))
