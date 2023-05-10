from datetime import date, timedelta
from dataclasses import asdict
from functools import cache
import json

from engie import EngieIndexingSetting, GAS_URL, ENERGY_URL


@cache
def get_index_values() -> list[EngieIndexingSetting]:
    """Get the list of values"""
    return EngieIndexingSetting.from_url(GAS_URL) + EngieIndexingSetting.from_url(ENERGY_URL)


def handler(event, _context):
    """The handler"""
    last_month = date.today().replace(day=1) - timedelta(days=1)
    req_index = event["INDEX"]
    req_year = event.get("YEAR", last_month.year)
    req_month = event.get("MONTH", last_month.month)
    index_values = get_index_values()

    result = [
        index_value
        for index_value in index_values
        if index_value.date.year == req_year and index_value.date.month == req_month and index_value.name == req_index
    ]
    if len(result) == 1:
        return {"statusCode": 200, "body": json.dumps(asdict(result[0]), default=str)}


if __name__ == "__main__":
    print(handler({"INDEX": "ZTP DAM"}, {}))
    print(handler({"INDEX": "Epex DAM"}, {}))
    print(handler({"INDEX": "ZTP DAM", "YEAR": 2023, "MONTH": 3}, {}))
    print(handler({"INDEX": "Epex DAM", "YEAR": 2023, "MONTH": 3}, {}))
