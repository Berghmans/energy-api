"""Data access object for grid costs"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Tuple
import hashlib

from dao.dynamodb import DaoDynamoDB


def divide_chunks(graduated: dict[int, float]):
    """Divide the list of keys in intervals"""
    keys = sorted(list(graduated.keys())) + [-1]
    for i in range(0, len(keys) - 1):
        yield (keys[i], keys[i + 1], graduated[keys[i]])


def calculate_graduation(graduated: dict[int, float], energy_usage: float):
    """Calculate the value given the graduaded values"""
    return sum([max((min(energy_usage, end) if end != -1 else energy_usage) - start, 0) * value for start, end, value in divide_chunks(graduated)])


@dataclass
class EnergyExcise(DaoDynamoDB):
    """Class that represents the tax levied on energy consumption"""

    country: str

    graduated_excise: dict[int, float]
    energy_contribution: float

    def _to_ddb_json(self):
        """Convert the current object to a JSON for storing in dynamodb"""

        primary, secondary = EnergyExcise._ddb_hash(self.country)
        return {
            **asdict(self),
            "primary": primary,
            "secondary": secondary,
            "energy_contribution": str(self.energy_contribution),
            "graduated_excise": {str(key): str(value) for key, value in self.graduated_excise.items()},
        }

    @staticmethod
    def _ddb_hash(country: str) -> Tuple[str, int]:
        """Get a hash for dynamodb"""
        primary = f"excise#{country}"
        secondary_int = int(hashlib.sha1(primary.encode(encoding="utf-8")).hexdigest()[-16:], 16)
        return (primary, secondary_int)

    @classmethod
    def _from_ddb_json(cls, data):
        """Parse the JSON from dynamodb and create the object"""
        return cls(
            country=data.get("country"),
            graduated_excise={int(key): float(value) for key, value in data.get("graduated_excise", {}).items()},
            energy_contribution=float(data.get("energy_contribution")),
        )

    @classmethod
    def load(cls, db_table, country: str) -> EnergyExcise:
        """Load the grid costs from the database"""
        primary, secondary = EnergyExcise._ddb_hash(country)
        return EnergyExcise.load_key(db_table=db_table, primary=primary, secondary=secondary)

    def calculate(self, total_energy_usage: float) -> float:
        """Calculate the excise given the total energy usage"""
        excise = calculate_graduation(self.graduated_excise, total_energy_usage)
        contribution = total_energy_usage * self.energy_contribution

        return round(excise + contribution, 3)
