"""Data access object for grid costs"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum, auto

from dao.dynamodb import DaoDynamoDB


class EnergyDirection(Enum):
    """The possible directions for energy"""

    DRAWDOWN = auto()
    INJECTION = auto()


@dataclass
class EnergyGridCost(DaoDynamoDB):
    """Class that represents a grid cost configuration"""

    country: str
    grid_provider: str
    direction: EnergyDirection

    peak_usage_avg_monthly_cost: float  # price for the monthly average usage
    peak_usage_kwh: float  # price per kWh for peak usage

    data_management_standard: float  # price for standard data management, i.e. monthly or yearly invoices with monthly price
    data_management_dynamic: float  # price for dynamic management, i.e. hourly prices

    public_services_kwh: float  # price per kWh for public services
    surcharges_kwh: float  # price per kWh for surcharges
    transmission_charges_kwh: float  # price per kWh for transmissions

    def _to_ddb_json(self):
        """Convert the current object to a JSON for storing in dynamodb"""

        def _convert_value(value):
            if isinstance(value, float):
                return str(value)
            if isinstance(value, EnergyDirection):
                return value.name
            return value

        data = {key: _convert_value(value) for key, value in asdict(self).items()}
        primary = f"energygridcost#{self.country}#{self.grid_provider}"
        return {
            **data,
            "primary": f"energygridcost#{self.country}#{self.grid_provider}",
            "secondary": hash(primary),
        }

    @classmethod
    def _from_ddb_json(cls, data):
        """Parse the JSON from dynamodb and create the object"""
        return cls(
            country=data.get("country"),
            grid_provider=data.get("grid_provider"),
            direction=EnergyDirection[data.get("direction")],
            peak_usage_avg_monthly_cost=float(data.get("peak_usage_avg_monthly_cost")),
            peak_usage_kwh=float(data.get("peak_usage_kwh")),
            data_management_standard=float(data.get("data_management_standard")),
            data_management_dynamic=float(data.get("data_management_dynamic")),
            public_services_kwh=float(data.get("public_services_kwh")),
            surcharges_kwh=float(data.get("surcharges_kwh")),
            transmission_charges_kwh=float(data.get("transmission_charges_kwh")),
        )

    @classmethod
    def load(cls, db_table, country: str, provider: str) -> EnergyGridCost:
        """Load the grid costs from the database"""
        primary = f"energygridcost#{country}#{provider}"
        return EnergyGridCost.load_key(db_table=db_table, primary=primary, secondary=hash(primary))

    def calculate(self, peak_power_usage: float, total_energy_usage: float, dynamic_data_management: bool) -> float:
        """Calculate the yearly price given the average monthly peak power usage and total energy usage"""
        if self.country == "BE" and self.direction == EnergyDirection.DRAWDOWN:
            energy_cost = total_energy_usage * (self.peak_usage_kwh + self.public_services_kwh + self.surcharges_kwh + self.transmission_charges_kwh)
            power_cost = peak_power_usage * self.peak_usage_avg_monthly_cost
            data_management_cost = self.data_management_dynamic if dynamic_data_management else self.data_management_standard

            return round(energy_cost + power_cost + data_management_cost, 3)

        raise NotImplementedError(f"Grid costs not implemented for this country and direction: {self.country} {self.direction.name}")
