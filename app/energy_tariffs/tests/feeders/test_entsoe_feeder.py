"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, call
from pathlib import Path
from datetime import datetime
from statistics import mean
import os

from moto import mock_dynamodb, mock_secretsmanager
import requests_mock
from pytz import utc, timezone

from feeders.entsoe import EntsoeIndexingSetting, ENTSOE_URL
from dao.indexingsetting import IndexingSettingOrigin, IndexingSettingTimeframe, IndexingSettingDocumentation
from lambda_feeder import entsoe_handler as handler
from tests.creators import create_dynamodb_table, create_secrets


def mock_url(mock, url: str, file_name: str):
    """Mock the URL to return some text that is stored in given file name"""
    with (Path(__file__).parent / "data" / file_name).open(mode="r", encoding="utf-8") as file_handle:
        html_text = file_handle.read()
    mock.get(url, text=html_text)


@requests_mock.Mocker()
class TestEEXIndexingSetting(TestCase):
    """Test class for EEXIndexingSetting"""

    def test_get_be_values(self, mock):
        """Test the get_ztp_values method"""
        mock_url(mock, ENTSOE_URL, "entsoe_be.xml")
        tz_be = timezone("Europe/Brussels")
        start = tz_be.localize(datetime(2023, 4, 1))
        end = tz_be.localize(datetime(2023, 5, 1))
        indexes = EntsoeIndexingSetting.get_be_values(api_key="key", start=start, end=end)
        self.assertEqual(
            f"{ENTSOE_URL}?documentType=A44&"
            "in_Domain=10YBE----------2&out_Domain=10YBE----------2"
            "&securityToken=key&periodStart=202303312200&periodEnd=202304302200",
            mock.request_history[0].url,
        )
        self.assertEqual(720, len(indexes))
        self.assertEqual(105.53447222222222, mean(index.value for index in indexes))
        start = tz_be.localize(datetime(2023, 4, 10))
        end = tz_be.localize(datetime(2023, 4, 12))
        indexes = EntsoeIndexingSetting.get_be_values(api_key="key", start=start, end=end)
        self.assertEqual(
            f"{ENTSOE_URL}?documentType=A44&"
            "in_Domain=10YBE----------2&out_Domain=10YBE----------2"
            "&securityToken=key&periodStart=202304092200&periodEnd=202304112200",
            mock.request_history[1].url,
        )
        self.assertEqual(48, len(indexes))
        self.assertEqual(65.99125, mean(index.value for index in indexes))

    def test_non_implemented_country(self, mock):
        """Test the query method with country out of scope"""
        mock_url(mock, ENTSOE_URL, "entsoe_be.xml")
        tz_be = timezone("Europe/Brussels")
        start = tz_be.localize(datetime(2023, 4, 1))
        end = tz_be.localize(datetime(2023, 5, 1))
        self.assertRaises(NotImplementedError, EntsoeIndexingSetting.query, api_key="key", country_code="FR", start=start, end=end)

    def test_no_matching_data_found(self, mock):
        """Test the query method with no matching data"""
        mock.get(ENTSOE_URL, text="No matching data found", headers={"content-type": "application/xml"})
        tz_be = timezone("Europe/Brussels")
        start = tz_be.localize(datetime(2023, 4, 1))
        end = tz_be.localize(datetime(2023, 5, 1))
        self.assertRaises(ValueError, EntsoeIndexingSetting.query, api_key="key", country_code="BE", start=start, end=end)


@mock_dynamodb
@mock_secretsmanager
class TestLambdaHandlerEntsoe(TestCase):
    """Test class for lambda entsoe feeder handler"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.secret = create_secrets()
        now = datetime.now(utc)
        self.indexes = [
            EntsoeIndexingSetting(
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
        with patch("feeders.entsoe.EntsoeIndexingSetting.query", return_value=self.indexes):
            os.environ["TABLE_NAME"] = self.db_table.name
            os.environ["SECRET_ARN"] = self.secret["ARN"]
            self.assertEqual(0, len(self.db_table.scan().get("Items", [])))
            handler({}, {})
            self.assertEqual(2, len(self.db_table.scan().get("Items", [])))
            self.assertEqual(1, len(IndexingSettingDocumentation.query(self.db_table)))

        with patch("feeders.entsoe.EntsoeIndexingSetting.query", return_value=self.indexes) as mock:
            handler({"start": "2023/04/01", "end": "2023/04/15"}, {})
            self.assertEqual(
                [call(api_key="fakekey", country_code="BE", start=datetime(2023, 4, 1, tzinfo=utc), end=datetime(2023, 4, 15, tzinfo=utc))], mock.mock_calls
            )
