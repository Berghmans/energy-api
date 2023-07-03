"""Test module for API classes"""
from __future__ import annotations

from moto import mock_dynamodb

from api.methods.excise import ExciseApiMethod
from dao.excise import EnergyExcise
from tests.creators import create_dynamodb_table
from tests.api_methods import TestCaseApiMethod


@mock_dynamodb
class TestExciseApiMethod(TestCaseApiMethod):
    """Test class for ExciseApiMethod"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.cost_obj = EnergyExcise(
            country="BE",
            graduated_excise={0: 0.0425755, 3000: 0.04748, 20000: 0.04546, 50000: 0.04478, 1000000: 0.04411, 25000000: 0.03628},
            energy_contribution=0.0019261,
        )
        self.cost_obj.save(self.db_table)
        self.assertIsNotNone(EnergyExcise.load(self.db_table, "BE"))

    def test_from_body_invalid(self):
        """Test the from_body method with invalid input"""
        self.assertBodyInvalid(ExciseApiMethod, {})

    def test_from_body_valid(self):
        """Test the from_body method"""
        self.assertBodyValid(
            ExciseApiMethod,
            {
                "COUNTRY": "BE",
                "ENERGY": 5000,
            },
        )

    def test_process(self):
        """Test the process method"""
        method = ExciseApiMethod(db_table=self.db_table, country="BE", energy_usage=5000.0)
        expected = {
            "country": "BE",
            "energy": 5000,
            "excise_cost": 232.317,
        }
        self.assertProcess(method, 200, expected)

    def test_from_body(self):
        """Test the from_body method"""
        method = ExciseApiMethod.from_body(
            self.db_table,
            {
                "COUNTRY": "BE",
                "ENERGY": 5000,
            },
        )
        expected = {
            "country": "BE",
            "energy": 5000,
            "excise_cost": 232.317,
        }
        self.assertProcess(method, 200, expected)

    def test_process_not_existing(self):
        """Test the process method for a not existing indexingsetting"""
        method = ExciseApiMethod.from_body(
            self.db_table,
            {
                "COUNTRY": "FR",
                "ENERGY": 5000,
            },
        )
        self.assertProcess(method, 400, {"error": "No result found for country"})
