"""
Module for getting EEX Spot Prices

https://www.eex.com/en/market-data/natural-gas/spot
"""
from dataclasses import dataclass
from datetime import datetime, date

import requests
from pytz import timezone

from dao import IndexingSetting, IndexingSettingOrigin, IndexingSettingTimeframe


EEX_URL = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/close/tradedatetimegmt/"


@dataclass
class EEXIndexingSetting(IndexingSetting):
    """Spot price of EEX"""

    @classmethod
    def from_eex_json(cls, index_name: str, timezone, data):
        """Parse from the EEX JSON"""
        date_time = datetime.strptime(data.get("tradedatetimegmt"), "%m/%d/%Y %H:%M:%S %p")
        date_time = timezone.localize(date_time)
        value = data.get("close")
        return cls(
            name=index_name.removeprefix("#E.").replace("_", " "),
            value=float(value) if value is not None and value != "" else None,
            timeframe=IndexingSettingTimeframe.DAILY,
            date=date_time.replace(hour=0, minute=0, second=0),
            source="EEX",
            origin=IndexingSettingOrigin.ORIGINAL,
        )

    @staticmethod
    def query(indexes: list[str], start: date, end: date, timezone):
        """Query"""
        session = requests.session()
        headers = {
            "Host": "webservice-eex.gvsi.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://www.eex.com",
            "Connection": "keep-alive",
            "Referer": "https://www.eex.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        session.headers = headers

        def sub_query(session, index: str, start: date, end: date) -> list[EEXIndexingSetting]:
            """Query for a single index"""
            response = session.get(
                EEX_URL,
                params={
                    "priceSymbol": f'"{index}"',
                    "chartstartdate": start.strftime("%Y/%m/%d"),
                    "chartstopdate": end.strftime("%Y/%m/%d"),
                    "dailybarinterval": "Days",
                    "aggregatepriceselection": "First",
                },
            )
            response.raise_for_status()
            return [EEXIndexingSetting.from_eex_json(index, timezone, item) for item in response.json().get("results", {}).get("items", [])]

        return [
            result
            for index in indexes
            for result in sub_query(session=session, index=index, start=start, end=end)
            if result.value is not None and result.date.date() >= start and result.date.date() <= end
        ]

    @staticmethod
    def get_ztp_values(date_filter: date, end: date = None):
        """Get the ZTP indexes since given datefilter"""
        return EEXIndexingSetting.query(
            indexes=["#E.ZTP_GTND", "#E.ZTP_GTWE"], start=date_filter, end=date.today() if end is None else end, timezone=timezone("Europe/Brussels")
        )
