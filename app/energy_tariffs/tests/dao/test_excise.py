"""Test module for IndexingSetting DAO"""
from __future__ import annotations
from unittest import TestCase

from moto import mock_dynamodb

from dao.excise import EnergyExcise, divide_chunks, calculate_graduation
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestEnergyExcise(TestCase):
    """Test class for EnergyExcise"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.cost_obj = EnergyExcise(
            country="BE",
            graduated_excise={0: 0.0425755, 3000: 0.04748, 20000: 0.04546, 50000: 0.04478, 1000000: 0.04411, 25000000: 0.03628},
            energy_contribution=0.0019261,
        )

    def test_divide_chunks(self):
        """Test the divide_chunks function"""
        self.assertEqual(
            [
                (0, 3000, 0.0425755),
                (3000, 20000, 0.04748),
                (20000, 50000, 0.04546),
                (50000, 1000000, 0.04478),
                (1000000, 25000000, 0.04411),
                (25000000, -1, 0.03628),
            ],
            list(divide_chunks(self.cost_obj.graduated_excise)),
        )

    def test_calculate_graduation(self):
        """Test the calculate_graduation function"""
        self.assertEqual(222.6865, round(calculate_graduation(self.cost_obj.graduated_excise, 5000), 4))

    def test_save(self):
        """Test the save method"""
        self.cost_obj.save(self.db_table)
        primary, secondary = EnergyExcise._ddb_hash("BE")
        response = self.db_table.get_item(
            Key={
                "primary": primary,
                "secondary": secondary,
            }
        )
        self.assertIn("Item", response)
        self.assertIn("primary", response["Item"])
        self.assertIn("secondary", response["Item"])
        self.assertEqual("0.0019261", response["Item"]["energy_contribution"])

    def test_save_list(self):
        """Test the save_list method"""
        obj2 = EnergyExcise(
            country="FR",
            graduated_excise={0: 0.0425755, 3000: 0.04748, 20000: 0.04546, 50000: 0.04478, 1000000: 0.04411, 25000000: 0.03628},
            energy_contribution=0.0019261,
        )
        EnergyExcise.save_list(self.db_table, [self.cost_obj, obj2])
        self.assertEqual(2, len(self.db_table.scan().get("Items", [])))

    def test_load(self):
        """Test the load method"""
        self.cost_obj.save(self.db_table)
        object = EnergyExcise.load(self.db_table, "BE")
        self.assertEqual("BE", object.country)
        self.assertEqual({0: 0.0425755, 3000: 0.04748, 20000: 0.04546, 50000: 0.04478, 1000000: 0.04411, 25000000: 0.03628}, object.graduated_excise)
        self.assertEqual(0.0019261, object.energy_contribution)

    def test_calculate(self):
        """Test the calculate method"""
        self.assertEqual(232.317, self.cost_obj.calculate(5000))
        self.assertEqual(479.348, self.cost_obj.calculate(10000))
