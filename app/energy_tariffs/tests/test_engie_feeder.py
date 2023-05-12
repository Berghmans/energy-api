"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from pathlib import Path

import requests_mock

from engie import EngieIndexingSetting
from dao import IndexingSettingTimeframe, IndexingSettingOrigin


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
