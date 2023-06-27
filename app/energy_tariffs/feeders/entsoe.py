"""Module for getting ENTSO-E SDAC prices (Single Day Ahead Coupling price)"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from bs4.element import Tag
import json

import requests
import boto3
from pytz import utc

from dao.indexingsetting import IndexingSetting, IndexingSettingOrigin, IndexingSettingTimeframe


ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"


@dataclass
class EntsoeIndexingSetting(IndexingSetting):
    """Single Day Ahead Coupling price of ENTSO-E"""

    @staticmethod
    def lookup_area_code(country_code: str) -> str:
        if country_code == "BE":
            return "10YBE----------2"
        raise NotImplementedError(f"Did not find area code for given country code {country_code}")

    @classmethod
    def from_entsoe_data(cls, index_name: str, date_time: datetime, value: float):
        """Parse from the ENTSOE data"""
        return cls(
            name=index_name,
            value=value,
            timeframe=IndexingSettingTimeframe.HOURLY,
            date=date_time.replace(minute=0, second=0),
            source="ENTSO-E",
            origin=IndexingSettingOrigin.ORIGINAL,
        )

    @staticmethod
    def iterate_timeseries(xml: str):
        """Iterate over all timeseries in the XML"""
        soup = BeautifulSoup(xml, features="xml")
        for timeseries in soup.find_all("TimeSeries"):
            yield EntsoeTimeSeries.from_xml(timeseries)

    @staticmethod
    def query(api_key: str, country_code: str, start: datetime, end: datetime):
        """Query"""
        area = EntsoeIndexingSetting.lookup_area_code(country_code=country_code)
        params = {
            "documentType": "A44",
            "in_Domain": area,
            "out_Domain": area,
            "securityToken": api_key,
            "periodStart": start.astimezone(utc).strftime("%Y%m%d%H00"),
            "periodEnd": end.astimezone(utc).strftime("%Y%m%d%H00"),
        }

        response = requests.get(url=ENTSOE_URL, params=params)
        response.raise_for_status()
        if response.headers.get("content-type", "") == "application/xml" and "No matching data found" in response.text:
            raise ValueError("Not expecting no data")

        return [
            EntsoeIndexingSetting.from_entsoe_data(f"SDAC {country_code}", timestamp, value)
            for timeserie in EntsoeIndexingSetting.iterate_timeseries(response.text)
            for timestamp, value in timeserie.to_period().items()
            if timestamp >= start and timestamp < end
        ]

    @staticmethod
    def get_be_values(api_key: str, start: datetime, end: datetime = None):
        """Get the Belgium SDAC"""
        return EntsoeIndexingSetting.query(api_key=api_key, country_code="BE", start=start, end=(datetime.now(utc) if end is None else end))

    @staticmethod
    def fetch_api_key(secret_arn: str) -> str:
        """Fetch the API key from AWS"""
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        value = json.loads(response["SecretString"])
        return value["ENTSOE_KEY"]


@dataclass
class EntsoeTimeSeries:
    """Class for a time series"""

    currency: str
    measure_unit: str
    start_time: datetime
    end_time: datetime
    resolution: str
    period: list[float]

    @classmethod
    def from_xml(cls, xml: Tag):
        """Parse the xml"""
        currency = xml.find("currency_Unit.name").text
        measure_unit = xml.find("price_Measure_Unit.name").text
        period = xml.find("Period")
        time_interval = period.find("timeInterval")
        start_time = time_interval.find("start").text
        end_time = time_interval.find("end").text
        resolution = period.find("resolution").text
        values_map = {int(point.find("position").text): float(point.find("price.amount").text) for point in period.find_all("Point")}
        values = [values_map[key] for key in sorted(values_map.keys(), reverse=False)]
        start_datetime = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_datetime = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        return cls(currency=currency, measure_unit=measure_unit, start_time=start_datetime, end_time=end_datetime, resolution=resolution, period=values)

    def to_period(self) -> dict[datetime, float]:
        return {self.start_time + timedelta(hours=i): value for i, value in enumerate(self.period)}
