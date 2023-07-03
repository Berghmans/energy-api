"""Module for the end price method"""
from dataclasses import dataclass
import logging
import json

from api.method import ApiMethod
from api.methods.indexing_setting import IndexingSettingApiMethod
from api.methods.grid_cost import GridCostApiMethod
from api.methods.excise import ExciseApiMethod
from api.result import ApiResult, Success, BadRequest


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class EndPriceApiMethod(ApiMethod):
    """Method for /endprice"""

    index: IndexingSettingApiMethod
    intercept: float
    slope: float
    taxes: float
    grid_costs: GridCostApiMethod = None
    excises: ExciseApiMethod = None

    def process(self) -> ApiResult:
        index_result = self.index.process()
        grid_cost_result = self.grid_costs.process() if self.grid_costs is not None else Success({"grid_cost": 0, "energy": 1})
        excise_result = self.excises.process() if self.excises is not None else Success({"excise_cost": 0, "energy": 1})

        if index_result.status_code == 200 and grid_cost_result.status_code == 200 and excise_result.status_code == 200:
            # Using linear regression Y = a + bX
            # a: the intercept, which the base cost of the unit
            # b: the slope of the line, which is the factor to be multiplied with the indexing setting value
            end_price = self.intercept + self.slope * index_result.body["value"]
            # Grid costs
            end_price += grid_cost_result.body["grid_cost"] / grid_cost_result.body["energy"]
            # Excises
            end_price += excise_result.body["excise_cost"] / excise_result.body["energy"]
            # Taxes
            end_price *= self.taxes

            result = {
                **index_result.body,
                "end_price": end_price,
                "grid": grid_cost_result.body,
                "excise": excise_result.body,
            }
            return Success(result)
        return BadRequest("No result found for requested index")

    @classmethod
    def from_body(cls, db_table, body: dict):
        """Create the object from a HTTP request body"""
        logger.info(f"Creating the {cls.__name__} method for body {json.dumps(body)}")
        if any(key not in body for key in ["INTERCEPT", "SLOPE", "TAXES"]):
            return None
        index = IndexingSettingApiMethod.from_body(db_table=db_table, body=body)
        if index is None:
            return None

        # Grid costs
        if "GRID" in body:
            grid_costs = GridCostApiMethod.from_body(db_table=db_table, body=body["GRID"])
            if grid_costs is None:
                return None
        else:
            grid_costs = None

        # Excises
        if "EXCISE" in body:
            excises = ExciseApiMethod.from_body(db_table=db_table, body=body["EXCISE"])
            if excises is None:
                return None
        else:
            excises = None

        intercept = body["INTERCEPT"]
        slope = body["SLOPE"]
        taxes = body["TAXES"]
        return cls(
            index=index,
            intercept=intercept,
            slope=slope,
            taxes=taxes,
            grid_costs=grid_costs,
            excises=excises,
        )
