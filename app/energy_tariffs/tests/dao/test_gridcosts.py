"""Test module for IndexingSetting DAO"""
from __future__ import annotations
from unittest import TestCase

from moto import mock_dynamodb

from dao.gridcost import EnergyGridCost, EnergyDirection
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestEnergyGridCost(TestCase):
    """Test class for EnergyGridCost"""

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

    def test_save(self):
        """Test the save method"""
        self.cost_obj.save(self.db_table)
        primary, secondary = EnergyGridCost._ddb_hash("BE", "Fluvius Antwerpen")
        response = self.db_table.get_item(
            Key={
                "primary": primary,
                "secondary": secondary,
            }
        )
        self.assertIn("Item", response)
        self.assertIn("primary", response["Item"])
        self.assertIn("secondary", response["Item"])
        self.assertEqual("DRAWDOWN", response["Item"]["direction"])

    def test_save_list(self):
        """Test the save_list method"""
        obj2 = EnergyGridCost(
            country="BE",
            grid_provider="Fluvius Limburg",
            direction=EnergyDirection.DRAWDOWN,
            peak_usage_avg_monthly_cost=37.7649625,
            peak_usage_kwh=0.00908,
            data_management_standard=12.63,
            data_management_dynamic=13.71,
            public_services_kwh=0.0215095,
            surcharges_kwh=0.0011539,
            transmission_charges_kwh=0.0035578,
        )
        EnergyGridCost.save_list(self.db_table, [self.cost_obj, obj2])
        self.assertEqual(2, len(self.db_table.scan().get("Items", [])))

    def test_load(self):
        """Test the load method"""
        self.cost_obj.save(self.db_table)
        object: EnergyGridCost = EnergyGridCost.load(self.db_table, "BE", "Fluvius Antwerpen")
        self.assertEqual("BE", object.country)
        self.assertEqual("Fluvius Antwerpen", object.grid_provider)
        self.assertEqual(EnergyDirection.DRAWDOWN, object.direction)
        self.assertEqual(37.7649625, object.peak_usage_avg_monthly_cost)

    def test_calculate(self):
        """Test the calculate method"""
        self.assertEqual(303.511, self.cost_obj.calculate(3, 5000, True))
        self.assertEqual(302.431, self.cost_obj.calculate(3, 5000, False))
        self.assertEqual(273.137, self.cost_obj.calculate(5, 2000, True))
        self.assertEqual(272.057, self.cost_obj.calculate(5, 2000, False))

        self.cost_obj.country = "FR"
        self.assertRaises(NotImplementedError, self.cost_obj.calculate, 3, 5000, True)
        self.cost_obj.country = "BE"
        self.assertEqual(303.511, self.cost_obj.calculate(3, 5000, True))
        self.cost_obj.direction = EnergyDirection.INJECTION
        self.assertRaises(NotImplementedError, self.cost_obj.calculate, 3, 5000, True)
