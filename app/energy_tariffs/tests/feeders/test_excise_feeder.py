"""Test module for lambda"""
from __future__ import annotations
from unittest import TestCase
import os

from moto import mock_dynamodb

from lambda_feeder import excises_handler as handler
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestLambdaHandlerExcises(TestCase):
    """Test class for lambda excises feeder handler"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()

    def test_handler(self):
        """Test the lambda handler"""
        os.environ["TABLE_NAME"] = self.db_table.name
        self.assertEqual(0, len(self.db_table.scan().get("Items", [])))
        handler({}, {})
        self.assertEqual(1, len(self.db_table.scan().get("Items", [])))
