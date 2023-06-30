"""Module for the indexing setting method"""
from dataclasses import dataclass
import logging
import json


from api.method import ApiMethod
from api.result import ApiResult
from dao.gridcost import EnergyGridCost


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class GridCostApiMethod(ApiMethod):
    """Method for /gridcost"""

    db_table: object  # Unfortunately not easy typing for boto3
    country: str
    provider: str
    power_usage: float  # in kW for the last year
    energy_usage: float  # in kWh for the last year
    dynamic: bool  # whether you have an hourly (True) or monthly/yearly measuring contract (False)

    def process(self) -> ApiResult:
        grid_cost = EnergyGridCost.load(db_table=self.db_table, country=self.country, provider=self.provider)

        if grid_cost is not None:
            return ApiResult(
                200,
                {
                    "grid_cost": grid_cost.calculate(
                        peak_power_usage=self.power_usage, total_energy_usage=self.energy_usage, dynamic_data_management=self.dynamic
                    )
                },
            )
        return ApiResult(400)

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if any([key not in body for key in ["COUNTRY", "PROVIDER", "POWER", "ENERGY", "DYNAMIC"]]):
            return None
        req_country = body["COUNTRY"]
        req_provider = body["PROVIDER"]
        req_power = body["POWER"]
        req_energy = body["ENERGY"]
        req_dynamic = body["DYNAMIC"]

        return cls(
            db_table=db_table,
            country=req_country,
            provider=req_provider,
            power_usage=req_power,
            energy_usage=req_energy,
            dynamic=req_dynamic,
        )
