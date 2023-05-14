"""Module for getting ENTSO-E SDAC prices (Single Day Ahead Coupling price)"""
from dataclasses import dataclass
from datetime import date, timedelta
import json

from pandas import Timestamp
from entsoe import EntsoePandasClient
import boto3

from dao import IndexingSetting, IndexingSettingOrigin, IndexingSettingTimeframe


@dataclass
class EntsoeIndexingSetting(IndexingSetting):
    """Single Day Ahead Coupling price of ENTSO-E"""

    @classmethod
    def from_entsoe_data(cls, index_name: str, date_time: Timestamp, value: float):
        """Parse from the ENTSOE data"""
        return cls(
            name=index_name,
            value=value,
            timeframe=IndexingSettingTimeframe.HOURLY,
            date=date_time.to_pydatetime().replace(tzinfo=None, minute=0, second=0),
            source="ENTSO-E",
            origin=IndexingSettingOrigin.ORIGINAL,
        )

    @staticmethod
    def query(api_key: str, country_code: str, start: date, end: date):
        """Query"""
        client = EntsoePandasClient(api_key=api_key)
        sdac_prices = client.query_day_ahead_prices(country_code, start=Timestamp(start, tz="Europe/Brussels"), end=Timestamp(end, tz="Europe/Brussels"))

        return [EntsoeIndexingSetting.from_entsoe_data(f"SDAC {country_code}", timestamp, value) for timestamp, value in sdac_prices.to_dict().items()]

    @staticmethod
    def get_be_values(api_key: str, date_filter: date, end: date = None):
        """Get the Belgium SDAC"""
        return EntsoeIndexingSetting.query(
            api_key=api_key, country_code="BE", start=date_filter, end=(date.today() if end is None else end) + timedelta(days=1)
        )

    @staticmethod
    def fetch_api_key(secret_arn: str) -> str:
        """Fetch the API key from AWS"""
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        value = json.loads(response["SecretString"])
        return value["ENTSOE_KEY"]
