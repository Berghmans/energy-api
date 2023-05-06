from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET


be_tz = pytz.timezone("Europe/Brussels")


@dataclass
class TimeSeries:
    """Class for a time series"""
    currency: str
    measure_unit: str
    start_time: datetime
    end_time: datetime
    resolution: str
    period: list[float]

    @classmethod
    def from_xml(cls, xml: ET.Element):
        """Parse the xml"""
        currency = xml.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}currency_Unit.name").text
        measure_unit = xml.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}price_Measure_Unit.name").text
        period = xml.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}Period")
        time_interval = period.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}timeInterval")
        start_time = time_interval.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}start").text
        end_time = time_interval.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}end").text
        resolution = period.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}resolution").text
        values_map = {
            int(point.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}position").text): float(point.find("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}price.amount").text)
            for point in period.findall("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}Point")
        }
        values = [values_map[key] for key in sorted(values_map.keys(), reverse=False)]
        start_datetime = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_datetime = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        return cls(
            currency=currency,
            measure_unit=measure_unit,
            start_time=start_datetime,
            end_time=end_datetime,
            resolution=resolution,
            period=values
        )
    
    def to_period(self) -> dict[str, float]:
        start_time = self.start_time.astimezone(be_tz)
        return {
            str(start_time + timedelta(hours=i)): value
            for i, value in enumerate(self.period)
        }
    
    def filter(self, month: int, year: int) -> bool:
        cmp_datetime = self.start_time.astimezone(be_tz)
        return cmp_datetime.month == month and cmp_datetime.year == year


@dataclass
class EngieIndexMonth:
    year: int
    month: int
    timeseries: list[TimeSeries]
    average: float = field(init=False)

    def __post_init__(self):
        values = [
            value
            for time_serie in self.timeseries
            if time_serie.filter(month=self.month, year=self.year)
            for value in time_serie.period
        ]
        self.average = sum(values) / len(values)


@dataclass
class EngiePriceMonth:
    fixed: float
    indexed: float
    indexation: float
    price: float = field(init=False)

    def __post_init__(self):
        self.price = self.fixed + self.indexed * self.indexation


# https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=true&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=01.04.2023+00:00|CET|DAY&biddingZone.values=CTY|10YBE----------2!BZN|10YBE----------2&resolution.values=PT60M&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)#
energy_prices = ET.parse('day_ahead_2023.xml')
energy_root = energy_prices.getroot()

timeseries = [
    TimeSeries.from_xml(child)
    for child in energy_root.iter("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}TimeSeries")
]


for i in range(1, 5):
    pricing_day = EngiePriceMonth(3.0326, 0.1229, EngieIndexMonth(2023, i, timeseries).average)
    pricing_day_rnd = round(pricing_day.price * 1.05 / 100, 3)
    pricing_night = EngiePriceMonth(2.9826, 0.0919, EngieIndexMonth(2023, i, timeseries).average)
    pricing_night_rnd = round(pricing_night.price * 1.05 / 100, 3)
    print(f"{pricing_day_rnd} - {pricing_night_rnd}")
