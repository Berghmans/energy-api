"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, call
from pathlib import Path
from datetime import datetime, date, timedelta
import os

import requests_mock
from moto import mock_dynamodb
from pytz import utc

from feeders.engie import EngieIndexingSetting, GAS_URL, ENERGY_URL, convert_month
from dao import IndexingSettingOrigin, IndexingSettingTimeframe, IndexingSetting
from lambda_feeder import engie_handler as handler
from tests.creators import create_dynamodb_table


def mock_url(mock, url: str, file_name: str):
    """Mock the URL to return some text that is stored in given file name"""
    with (Path(__file__).parent / "data" / file_name).open(mode="r", encoding="utf-8") as file_handle:
        html_text = file_handle.read()
    mock.get(url, text=html_text)


@requests_mock.Mocker()
class TestEngieIndexingSetting(TestCase):
    """Test class for EngieIndexingSetting"""

    def test_convert_month(self, mock):
        """Test the convert_month method"""
        self.assertEqual(5, convert_month("May"))
        self.assertEqual(5, convert_month("mei"))
        self.assertEqual(4, convert_month("april"))
        self.assertRaises(ValueError, convert_month, "avril")

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
        indexes = EngieIndexingSetting.get_gas_values(date_filter=date(2023, 4, 1))
        self.assertEqual(8, len(indexes))

    def test_get_energy_values(self, mock):
        """Test the get_energy_values method"""
        mock_url(mock, ENERGY_URL, "engie_energy.html")
        indexes = EngieIndexingSetting.get_energy_values()
        self.assertEqual(109, len(indexes))
        indexes = EngieIndexingSetting.get_energy_values(date_filter=date(2023, 4, 1))
        self.assertEqual(7, len(indexes))

    @mock_dynamodb
    def test_calculate_derived_values(self, mock):
        """Test the calculate_derived_values method"""
        self.db_table = create_dynamodb_table()
        indexes = EngieIndexingSetting.calculate_derived_values(self.db_table, calculation_date=date(2023, 4, 30))
        self.assertEqual(0, len(indexes))
        sources = [
            IndexingSetting(
                name="SDAC BE",
                value=1.0,
                timeframe=IndexingSettingTimeframe.HOURLY,
                date=datetime(2023, 4, 1, 1, tzinfo=utc),
                source="ENTSO-E",
                origin=IndexingSettingOrigin.ORIGINAL,
            ),
            IndexingSetting(
                name="SDAC BE",
                value=2.0,
                timeframe=IndexingSettingTimeframe.HOURLY,
                date=datetime(2023, 4, 10, 1, tzinfo=utc),
                source="ENTSO-E",
                origin=IndexingSettingOrigin.ORIGINAL,
            ),
        ]
        IndexingSetting.save_list(self.db_table, sources)
        indexes = EngieIndexingSetting.calculate_derived_values(self.db_table, calculation_date=date(2023, 4, 30))
        self.assertEqual(1, len(indexes))
        self.assertEqual("Epex DAM", indexes[0].name)
        self.assertEqual(1.5, indexes[0].value)

        with patch("feeders.engie.IndexingSetting.query", return_value=[]):
            indexes = EngieIndexingSetting.calculate_derived_values(self.db_table)
            self.assertEqual(0, len(indexes))


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
                datetime(now.year, now.month, 1, tzinfo=utc),
                "src",
                IndexingSettingOrigin.ORIGINAL,
            )
        ]
        self.energy_indexes = [
            EngieIndexingSetting(
                "index2",
                1.1,
                IndexingSettingTimeframe.MONTHLY,
                datetime(now.year, now.month, 1, tzinfo=utc),
                "src",
                IndexingSettingOrigin.ORIGINAL,
            )
        ]
        self.derived_indexes = [
            EngieIndexingSetting(
                "index3",
                1.1,
                IndexingSettingTimeframe.MONTHLY,
                datetime(now.year, now.month, 1, tzinfo=utc),
                "src",
                IndexingSettingOrigin.DERIVED,
            )
        ]

    def test_handler(self):
        """Test the lambda handler"""
        # Path these methods so they return a fixed result, as the lambda handler is "moving"
        # and otherwise we would have no consistent results the coming months
        with patch("feeders.engie.EngieIndexingSetting.get_gas_values", return_value=self.gas_indexes), patch(
            "feeders.engie.EngieIndexingSetting.get_energy_values", return_value=self.energy_indexes
        ), patch("feeders.engie.EngieIndexingSetting.calculate_derived_values", return_value=self.derived_indexes):
            os.environ["TABLE_NAME"] = self.db_table.name
            self.assertEqual(0, len(self.db_table.scan().get("Items", [])))
            handler({}, {})
            self.assertEqual(3, len(self.db_table.scan().get("Items", [])))

        with patch("feeders.engie.EngieIndexingSetting.get_gas_values", return_value=[]) as mock_gas, patch(
            "feeders.engie.EngieIndexingSetting.get_energy_values", return_value=[]
        ) as mock_energy, patch("feeders.engie.EngieIndexingSetting.calculate_derived_values", return_value=[]) as mock_derived:
            handler({"start": "2023/04/01"}, {})
            self.assertEqual([call(date(2023, 4, 1))], mock_gas.mock_calls)
            self.assertEqual([call(date(2023, 4, 1))], mock_energy.mock_calls)
            self.assertEqual([call(self.db_table, None)], mock_derived.mock_calls)

        with patch("feeders.engie.EngieIndexingSetting.get_gas_values", return_value=[]) as mock_gas, patch(
            "feeders.engie.EngieIndexingSetting.get_energy_values", return_value=[]
        ) as mock_energy, patch("feeders.engie.EngieIndexingSetting.calculate_derived_values", return_value=[]) as mock_derived:
            handler({"calculate": "2023/04/30"}, {})
            self.assertEqual([call(date.today() - timedelta(days=90))], mock_gas.mock_calls)
            self.assertEqual([call(date.today() - timedelta(days=90))], mock_energy.mock_calls)
            self.assertEqual([call(self.db_table, date(2023, 4, 30))], mock_derived.mock_calls)
