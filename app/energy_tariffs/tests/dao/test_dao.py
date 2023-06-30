"""Test module for IndexingSetting DAO"""
from __future__ import annotations
from unittest import TestCase

from moto import mock_dynamodb

from dao.indexingsetting import DaoDynamoDB


@mock_dynamodb
class TestDaoDynamoDB(TestCase):
    """Test class for DaoDynamoDB"""

    def test_not_implemented(self):
        """Test the methods to be implemented"""
        self.assertRaises(NotImplementedError, DaoDynamoDB._from_ddb_json, {})
        self.assertRaises(NotImplementedError, DaoDynamoDB()._to_ddb_json)
