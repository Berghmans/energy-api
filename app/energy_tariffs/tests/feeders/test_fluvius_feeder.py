"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, call
from pathlib import Path

import requests_mock

from feeders.fluvius import FluviusParser, extract_excel_url
from dao.gridcost import EnergyDirection


def mock_url(mock, url: str, file_name: str):
    """Mock the URL to return some text that is stored in given file name"""
    file_path = Path(__file__).parent / "data" / file_name
    if file_path.suffix == ".xlsx":
        with file_path.open(mode="rb") as file_handle:
            bytes = file_handle.read()
        mock.get(url, content=bytes)
    else:
        with file_path.open(mode="r", encoding="utf-8") as file_handle:
            html_text = file_handle.read()
        mock.get(url, text=html_text)


@requests_mock.Mocker()
class TestFluviusGridCosts(TestCase):
    """Test class for Fluvius grid costs"""

    excel_url: str = "https://www.fluvius.be/sites/fluvius/files/2022-11/distributienettarieven-elektriciteit-afname-fluvius-antwerpen-01012023-31122023.xlsx"
    redirect_url: str = "https://www.fluvius.be/nl/publicatie/fluvius-antwerpen-distributienettarief-afname-elektriciteit-01012023-31122023"

    @patch("feeders.fluvius.FluviusParser.from_excel")
    @patch("feeders.fluvius.extract_excel_url", return_value=excel_url)
    def test_from_url(self, mock, mock_extract, mock_parser):
        """Test the from_url method"""
        mock_url(mock, FluviusParser.url, "fluvius_grid_costs.html")
        mock_url(mock, self.excel_url, "fluvius_excel_redirect.html")
        FluviusParser.from_url()
        self.assertEqual(
            [
                call("https://www.fluvius.be/nl/publicatie/fluvius-antwerpen-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-limburg-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-west-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/gaselwest-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/imewo-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/intergem-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iveka-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iverlek-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/pbe-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/sibelgas-distributienettarief-afname-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-antwerpen-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-limburg-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-west-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/gaselwest-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/imewo-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/intergem-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iveka-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iverlek-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/pbe-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/sibelgas-distributienettarief-injectie-elektriciteit-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-antwerpen-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-limburg-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-west-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/gaselwest-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/imewo-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/intergem-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iveka-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iverlek-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/sibelgas-distributienettarief-afname-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-antwerpen-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-limburg-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/fluvius-west-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/gaselwest-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/imewo-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/intergem-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iveka-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/iverlek-distributienettarief-injectie-aardgas-01012023-31122023"),
                call("https://www.fluvius.be/nl/publicatie/sibelgas-distributienettarief-injectie-aardgas-01012023-31122023"),
            ],
            mock_extract.mock_calls,
        )
        self.assertEqual(
            [
                call("Elektriciteit", "Afname", "Fluvius Antwerpen", self.excel_url),
                call("Elektriciteit", "Afname", "Fluvius Limburg", self.excel_url),
                call("Elektriciteit", "Afname", "Fluvius West", self.excel_url),
                call("Elektriciteit", "Afname", "GASELWEST", self.excel_url),
                call("Elektriciteit", "Afname", "IMEWO", self.excel_url),
                call("Elektriciteit", "Afname", "INTERGEM", self.excel_url),
                call("Elektriciteit", "Afname", "IVEKA", self.excel_url),
                call("Elektriciteit", "Afname", "IVERLEK", self.excel_url),
                call("Elektriciteit", "Afname", "PBE", self.excel_url),
                call("Elektriciteit", "Afname", "SIBELGAS", self.excel_url),
                call("Elektriciteit", "Injectie", "Fluvius Antwerpen", self.excel_url),
                call("Elektriciteit", "Injectie", "Fluvius Limburg", self.excel_url),
                call("Elektriciteit", "Injectie", "Fluvius West", self.excel_url),
                call("Elektriciteit", "Injectie", "GASELWEST", self.excel_url),
                call("Elektriciteit", "Injectie", "IMEWO", self.excel_url),
                call("Elektriciteit", "Injectie", "INTERGEM", self.excel_url),
                call("Elektriciteit", "Injectie", "IVEKA", self.excel_url),
                call("Elektriciteit", "Injectie", "IVERLEK", self.excel_url),
                call("Elektriciteit", "Injectie", "PBE", self.excel_url),
                call("Elektriciteit", "Injectie", "SIBELGAS", self.excel_url),
                call("Aardgas", "Afname", "Fluvius Antwerpen", self.excel_url),
                call("Aardgas", "Afname", "Fluvius Limburg", self.excel_url),
                call("Aardgas", "Afname", "Fluvius West", self.excel_url),
                call("Aardgas", "Afname", "GASELWEST", self.excel_url),
                call("Aardgas", "Afname", "IMEWO", self.excel_url),
                call("Aardgas", "Afname", "INTERGEM", self.excel_url),
                call("Aardgas", "Afname", "IVEKA", self.excel_url),
                call("Aardgas", "Afname", "IVERLEK", self.excel_url),
                call("Aardgas", "Afname", "SIBELGAS", self.excel_url),
                call("Aardgas", "Injectie", "Fluvius Antwerpen", self.excel_url),
                call("Aardgas", "Injectie", "Fluvius Limburg", self.excel_url),
                call("Aardgas", "Injectie", "Fluvius West", self.excel_url),
                call("Aardgas", "Injectie", "GASELWEST", self.excel_url),
                call("Aardgas", "Injectie", "IMEWO", self.excel_url),
                call("Aardgas", "Injectie", "INTERGEM", self.excel_url),
                call("Aardgas", "Injectie", "IVEKA", self.excel_url),
                call("Aardgas", "Injectie", "IVERLEK", self.excel_url),
                call("Aardgas", "Injectie", "SIBELGAS", self.excel_url),
            ],
            mock_parser.mock_calls,
        )

    def test_extract_excel_url(self, mock):
        """Test the extract_excel_url function"""
        mock_url(mock, self.redirect_url, "fluvius_excel_redirect.html")
        return_url = extract_excel_url(self.redirect_url)
        self.assertEqual(self.excel_url, return_url)

    def test_from_excel(self, mock):
        """Test the from_excel method"""
        mock_url(mock, self.excel_url, "fluvius_elec_drawdown_2023.xlsx")
        grid_costs = FluviusParser.from_excel("Elektriciteit", "Afname", "Fluvius Antwerpen", self.excel_url)
        self.assertEqual("BE", grid_costs.country)
        self.assertEqual("Fluvius Antwerpen", grid_costs.grid_provider)
        self.assertEqual(EnergyDirection.DRAWDOWN, grid_costs.direction)
        self.assertEqual(37.7649625, grid_costs.peak_usage_avg_monthly_cost)
        self.assertEqual(0.0090800, grid_costs.peak_usage_kwh)
        self.assertEqual(12.63, grid_costs.data_management_standard)
        self.assertEqual(13.71, grid_costs.data_management_dynamic)
        self.assertEqual(0.0215095, grid_costs.public_services_kwh)
        self.assertEqual(0.0011539, grid_costs.surcharges_kwh)
        self.assertEqual(0.0035578, grid_costs.transmission_charges_kwh)

        self.assertIsNotNone(FluviusParser.from_excel("Elektriciteit", "Drawdown", "Fluvius Antwerpen", self.excel_url))
        self.assertIsNone(FluviusParser.from_excel("Elektriciteit", "Injectie", "Fluvius Antwerpen", self.excel_url))
        self.assertIsNone(FluviusParser.from_excel("Gas", "Afname", "Fluvius Antwerpen", self.excel_url))
