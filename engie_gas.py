from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import locale

def convert_month(month: str) -> int:
    """Convert the month"""
    for language in ["nl_NL", "en_US"]:
        try:
            locale.setlocale(locale.LC_ALL, "nl_NL")
            return datetime.strptime(month, "%B").month
        except ValueError:
            pass
    return ValueError("Not able to translate")

@dataclass
class IndexValue:
    month: str
    year: int
    index: str
    value: float

    @classmethod
    def from_cell(cls, month, year, cell):
        """"""
        index_value = cell.select_one("span.table_mobile_header p strong").text
        data_span = cell.select_one("span.table_mobile_data")
        value = data_span.get_text().strip()

        return cls(
            month=convert_month(month),
            year=year,
            index=index_value,
            value=float(value.replace(",", ".")) if value is not None and value != "" else None
        )

    @staticmethod
    def from_row(row):
        if len(row) == 0:
            return []
        date_cell = row[0]
        data_value = date_cell.select_one("span div p").text
        if not "kwartaal" in data_value:
            month, year = data_value.replace(u'\xa0', ' ').split(" ")
            values = [
                IndexValue.from_cell(month, int(year), cell)
                for cell in row[1:]
            ]
            return list(filter(lambda item: item is not None and item.value is not None, values))
        else:
            return []

    @staticmethod
    def from_url(url):
        """Parse the values from URL"""
        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, 'html.parser')

        table = soup.find("div", class_="table_body")
        return [
            index_value
            for row in table.find_all("div", class_="table_row")
            for index_value in IndexValue.from_row(row.find_all("div", class_="table_cell"))
        ]

gas_url = 'https://www.engie.be/nl/professionals/energie/elektriciteit-gas/prijzen-voorwaarden/indexatieparameters/indexatieparameters-gas/'
ele_url = "https://www.engie.be/nl/professionals/energie/elektriciteit-gas/prijzen-voorwaarden/indexatieparameters/indexatieparameters-elektriciteit/"

gas_index_values = IndexValue.from_url(gas_url)
ele_index_values = IndexValue.from_url(ele_url)

print([
    index_value
    for index_value in gas_index_values
    if index_value.year == 2023 and index_value.index == "ZTP DAM"
])
print([
    index_value
    for index_value in ele_index_values
    if index_value.year == 2023 and index_value.index == "Epex DAM"
])
