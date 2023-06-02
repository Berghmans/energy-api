"""Module for retrieving the indexation parameters from Engie"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
import locale
import logging

from bs4 import BeautifulSoup
import requests
from pytz import timezone
import holidays

from dao import IndexingSetting, IndexingSettingOrigin, IndexingSettingTimeframe


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ENGIE_PREFIX_URL = "https://www.engie.be/nl/professionals/energie/elektriciteit-gas/prijzen-voorwaarden/indexatieparameters"
GAS_URL = f"{ENGIE_PREFIX_URL}/indexatieparameters-gas/"
ENERGY_URL = f"{ENGIE_PREFIX_URL}/indexatieparameters-elektriciteit/"


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
    raise ValueError("Not able to translate")


def is_holiday(day: datetime) -> bool:
    """Check if a day is a holiday"""
    return (
        day in holidays.country_holidays(country="BE", years=day.year)
        or day in holidays.country_holidays(country="NL", years=day.year)
        or day in holidays.country_holidays(country="DE", years=day.year)
        or day in holidays.country_holidays(country="FR", years=day.year)
    )


def get_last_weekday(day: datetime) -> datetime:
    """Get the last weekday that is not a holiday"""
    day_before = day - timedelta(days=1)
    if day_before.weekday() > 4:
        return get_last_weekday(day_before)
    if is_holiday(day_before):
        return get_last_weekday(day_before)
    return day_before


@dataclass
class EngieIndexingSetting(IndexingSetting):
    """Indexing Setting class for Engie"""

    @classmethod
    def from_cell(cls, month, year, cell):
        """Parse the value from a table cell"""
        index_name = cell.select_one("span.table_mobile_header p strong").text
        data_span = cell.select_one("span.table_mobile_data")
        value = data_span.get_text().strip()
        date_time = timezone("Europe/Brussels").localize(datetime(year, convert_month(month), 1))
        return cls(
            name=index_name.replace(")", "").replace("(", ""),
            value=float(value.replace(",", ".")) if value is not None and value != "" else None,
            timeframe=IndexingSettingTimeframe.MONTHLY,
            date=date_time,
            source="Engie",
            origin=IndexingSettingOrigin.ORIGINAL,
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

    @staticmethod
    def get_gas_values(date_filter: datetime = None):
        """Scrape the GAS indexing settings from the Engie website"""
        index_values = EngieIndexingSetting.from_url(GAS_URL)
        return [index_value for index_value in index_values if (date_filter is None or index_value.date >= date_filter)]

    @staticmethod
    def get_energy_values(date_filter: datetime = None):
        """Scrape the ENERGY indexing settings from the Engie website"""
        index_values = EngieIndexingSetting.from_url(ENERGY_URL)
        return [index_value for index_value in index_values if (date_filter is None or index_value.date >= date_filter)]

    @staticmethod
    def calculate_derived_values(db_table, calculation_date: datetime = None) -> list[IndexingSetting]:
        """Calculate a list of derived indexing settings"""
        tz_be = timezone("Europe/Brussels")
        indexes = []
        if calculation_date is None:
            calculation_date = datetime.now(tz_be)
        elif calculation_date.tzinfo is None:
            calculation_date = tz_be.localize(calculation_date)

        # EPEX DAM
        # De indexatieparameter is het rekenkundig gemiddelde van de dagelijkse quoteringen Day Ahead EPEX SPOT Belgium
        # (hierna EPEX DAM) tijdens de maand van levering. De dagelijkse quoteringen EPEX DAM worden uitgedrukt in €/MWh.
        # De waarde van EPEX DAM van de lopende maand zal pas gekend zijn aan het einde van de maand.
        tomorrow = calculation_date + timedelta(days=1)
        if tomorrow.month > calculation_date.month:
            # Tomorrow is a new month so calculate the values for EPEX DAM
            epex_dam = EngieIndexingSetting._calculate_epex_dam(db_table, calculation_date, tz_be, tomorrow)
            if epex_dam is not None:
                indexes.append(epex_dam)

            # Calculate the values for ZTP DAM
            ztp_dam = EngieIndexingSetting._calculate_ztp_dam(db_table, calculation_date, tz_be, tomorrow)
            if ztp_dam is not None:
                indexes.append(ztp_dam)

        return indexes

    @staticmethod
    def _calculate_epex_dam(db_table, calculation_date, tz_be, tomorrow):
        """Calculate the EPEX DAM derived indexing setting"""
        logger.info("Calculating values for EPEX DAM")
        start = calculation_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        index_values_month = IndexingSetting.query(
            db_table=db_table,
            source="ENTSO-E",
            name="SDAC BE",
            timeframe=IndexingSettingTimeframe.HOURLY,
            start=start,
            end=end,
        )
        if len(index_values_month) > 0:
            # Only calculate if we found results
            value = round(mean(index.value for index in index_values_month), 2)
            epex_dam = EngieIndexingSetting(
                name="Epex DAM",
                value=value,
                timeframe=IndexingSettingTimeframe.MONTHLY,
                date=tz_be.localize(datetime(calculation_date.year, calculation_date.month, 1)),
                source="Engie",
                origin=IndexingSettingOrigin.DERIVED,
            )
            logger.info(f"EPEX DAM: {value} (records: {len(index_values_month)})")
            return epex_dam
        return None

    @staticmethod
    def _calculate_ztp_dam(db_table, calculation_date, tz_be, tomorrow):
        """Calculate the ZTP DAM derived indexing setting"""
        logger.info("Calculating values for ZTP DAM")
        # start is 7 dyas before the beginning of this month so we make sure
        # we have the weekend values if the month starts with a weekend
        start = calculation_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
        end = tomorrow.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        ztp_weekends = IndexingSetting.query(
            db_table=db_table,
            source="EEX",
            name="ZTP GTWE",
            origin=IndexingSettingOrigin.ORIGINAL,
            timeframe=IndexingSettingTimeframe.DAILY,
            start=start,
            end=end,
        )
        ztp_days = IndexingSetting.query(
            db_table=db_table,
            source="EEX",
            name="ZTP GTND",
            origin=IndexingSettingOrigin.ORIGINAL,
            timeframe=IndexingSettingTimeframe.DAILY,
            start=start,
            end=end,
        )
        if len(ztp_weekends) == 0 or len(ztp_days) == 0:
            return None

        def get_ztp_value_for_day(day: datetime) -> float:
            """Get the ZTP value for a given day"""
            if day.weekday() <= 4:
                # A week day so we need ZTP Next Day
                for ztp_day in ztp_days:
                    if ztp_day.date == day:
                        logger.debug(f"Found ZTP GTND value for day {day}: {ztp_day.value}")
                        return ztp_day.value

            if day.weekday() > 4 or is_holiday(day):
                # A weekend day or holiday so we need ZTP Weekend
                day_before = get_last_weekday(day)
                for ztp_weekend in ztp_weekends:
                    if ztp_weekend.date == day_before:
                        logger.debug(f"Found ZTP GTWE value for day {day} from {ztp_weekend.date}: {ztp_weekend.value}")
                        return ztp_weekend.value

            raise ValueError(f"No ZTP value found for day {day}")

        try:
            month_values = [get_ztp_value_for_day(calculation_date.replace(day=day + 1)) for day in range(end.day)]
            return EngieIndexingSetting(
                name="ZTP DAM",
                value=round(mean(month_values), 2),
                timeframe=IndexingSettingTimeframe.MONTHLY,
                date=tz_be.localize(datetime(calculation_date.year, calculation_date.month, 1)),
                source="Engie",
                origin=IndexingSettingOrigin.DERIVED,
            )
        except ValueError as exc:
            logger.error(exc.args[0])
            return None
