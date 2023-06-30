"""Test module for API classes"""
from __future__ import annotations

from moto import mock_dynamodb

from api.methods.grid_cost import GridCostApiMethod
from dao.gridcost import EnergyGridCost, EnergyDirection
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestIndexingSettingApiMethod(TestCaseApiMethod):
    """Test class for IndexingSettingApiMethod"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.cost_obj = EnergyGridCost(
            country="BE",
            grid_provider="Fluvius Antwerpen",
            direction=EnergyDirection.DRAWDOWN,
            peak_usage_avg_monthly_cost=37.7649625,
            peak_usage_kwh=0.00908,
            data_management_standard=12.63,
            data_management_dynamic=13.71,
            public_services_kwh=0.0215095,
            surcharges_kwh=0.0011539,
            transmission_charges_kwh=0.0035578,
        )
        self.cost_obj.save(self.db_table)
        self.assertIsNotNone(EnergyGridCost.load(self.db_table, "BE", "Fluvius Antwerpen"))

    def test_from_body_invalid(self):
        """Test the from_body method with invalid input"""
        self.assertBodyInvalid(GridCostApiMethod, {})

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertBodyValid(
            GridCostApiMethod,
            {
                "COUNTRY": "BE",
                "PROVIDER": "Fluvius Antwerpen",
                "POWER": 3,
                "ENERGY": 5000,
                "DYNAMIC": True,
            },
        )

    def test_process(self):
        """Test the process method"""
        method = GridCostApiMethod(db_table=self.db_table, country="BE", provider="Fluvius Antwerpen", power_usage=3.0, energy_usage=5000.0, dynamic=True)
        expected = {
            "country": "BE",
            "provider": "Fluvius Antwerpen",
            "power": 3,
            "energy": 5000,
            "dynamic": True,
            "grid_cost": 303.511,
        }
        self.assertProcess(method, 200, expected)

    def test_from_body(self):
        """Test the from_body method"""
        method = GridCostApiMethod.from_body(
            self.db_table,
            {
                "COUNTRY": "BE",
                "PROVIDER": "Fluvius Antwerpen",
                "POWER": 3,
                "ENERGY": 5000,
                "DYNAMIC": True,
            },
        )
        expected = {
            "country": "BE",
            "provider": "Fluvius Antwerpen",
            "power": 3,
            "energy": 5000,
            "dynamic": True,
            "grid_cost": 303.511,
        }
        self.assertProcess(method, 200, expected)

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        method = GridCostApiMethod.from_body(
            self.db_table,
            {
                "COUNTRY": "BE",
                "PROVIDER": "Fluvius Limburg",
                "POWER": 3,
                "ENERGY": 5000,
                "DYNAMIC": True,
            },
        )
        self.assertProcess(method, 400, {"error": "No result found for grid provider"})
