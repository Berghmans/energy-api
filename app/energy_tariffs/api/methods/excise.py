"""Module for the indexing setting method"""
from dataclasses import dataclass
import logging
import json


from api.method import ApiMethod
from api.result import ApiResult, Success, BadRequest
from dao.excise import EnergyExcise


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class ExciseApiMethod(ApiMethod):
    """Method for /excise"""

    db_table: object  # Unfortunately not easy typing for boto3
    country: str
    energy_usage: float  # in kWh

    def process(self) -> ApiResult:
        excise = EnergyExcise.load(db_table=self.db_table, country=self.country)

        if excise is not None:
            return Success(
                {
                    "country": self.country,
                    "energy": self.energy_usage,
                    "excise_cost": excise.calculate(total_energy_usage=self.energy_usage),
                },
            )
        return BadRequest("No result found for country")

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if any([key not in body for key in ["COUNTRY", "ENERGY"]]):
            return None
        req_country = body["COUNTRY"]
        req_energy = body["ENERGY"]

        return cls(
            db_table=db_table,
            country=req_country,
            energy_usage=req_energy,
        )
