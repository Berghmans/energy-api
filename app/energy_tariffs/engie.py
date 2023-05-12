"""Module for retrieving the indexation parameters from Engie"""
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import locale

from dao import IndexingSetting
import dao


GAS_URL = "https://www.engie.be/nl/professionals/energie/elektriciteit-gas/prijzen-voorwaarden/indexatieparameters/indexatieparameters-gas/"
ENERGY_URL = "https://www.engie.be/nl/professionals/energie/elektriciteit-gas/prijzen-voorwaarden/indexatieparameters/indexatieparameters-elektriciteit/"


def convert_month(month: str) -> int:
    """Convert the month in a numeric value"""
    original = locale.getlocale()
    for language in ["nl_BE.UTF-8", "en_US.UTF-8"]:
        try:
            locale.setlocale(locale.LC_ALL, language)
            result = datetime.strptime(month, "%B").month
            locale.setlocale(locale.LC_ALL, original)
            return result
        except ValueError:
            pass
    locale.setlocale(locale.LC_ALL, original)
    return ValueError("Not able to translate")


@dataclass
class EngieIndexingSetting(IndexingSetting):
    """Indexing Setting class for Engie"""

    @classmethod
    def from_cell(cls, month, year, cell):
        """Parse the value from a table cell"""
        index_name = cell.select_one("span.table_mobile_header p strong").text
        data_span = cell.select_one("span.table_mobile_data")
        value = data_span.get_text().strip()
        return cls(
            name=index_name,
            value=float(value.replace(",", ".")) if value is not None and value != "" else None,
            timeframe=dao.MONTHLY,
            date=datetime(year, convert_month(month), 1),
            source="Engie",
            origin=dao.ORIGINAL,
        )

    @staticmethod
    def from_row(row):
        """Parse the indexation parameters from a table row"""
        if len(row) == 0:
            return []
        date_cell = row[0]
        data_value = date_cell.select_one("span div p").text
        if "kwartaal" not in data_value:
            month, year = data_value.replace("\xa0", " ").split(" ")
            values = [EngieIndexingSetting.from_cell(month, int(year), cell) for cell in row[1:]]
            return list(filter(lambda item: item is not None and item.value is not None, values))
        else:
            return []

    @staticmethod
    def from_url(url):
        """Parse the values from URL"""
        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, "html.parser")

        table = soup.find("div", class_="table_body")
        return [
            index_value
            for row in table.find_all("div", class_="table_row")
            for index_value in EngieIndexingSetting.from_row(row.find_all("div", class_="table_cell"))
        ]
