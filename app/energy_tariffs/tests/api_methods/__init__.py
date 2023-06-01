"""Mmodule for API test methods"""
from __future__ import annotations
from typing import Type
from unittest import TestCase
from pathlib import Path
import json

from api.method import ApiMethod


class TestCaseApiMethod(TestCase):
    """Class for testing an API method"""

    def save_db(self, db_table, file_name: str):
        """Save the database"""
        with (Path(__file__).parent / "data" / file_name).open(mode="w", encoding="utf-8") as file_handle:
            data = db_table.scan().get("Items", [])
            json.dump(data, file_handle, default=str)

    def load_db(self, db_table, file_name: str):
        """Save the database"""
        with (Path(__file__).parent / "data" / file_name).open(mode="r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        with db_table.batch_writer() as batch:
            for object in data:
                batch.put_item(Item={**object, "secondary": int(object["secondary"])})

    def assertBodyInvalid(self, cls: Type[ApiMethod], body: dict):
        """Test the from_body method with invalid input"""
        self.assertIsNone(cls.from_body(None, body))

    def assertBodyValid(self, cls: Type[ApiMethod], body: dict):
        """Test the from_body method"""
        self.assertIsNotNone(cls.from_body(None, body))

    def assertProcess(self, method: ApiMethod, status_code: int, expected: dict):
        """Test the process method"""
        self.assertIsNotNone(method)
        result = method.process()
        self.assertEqual(status_code, result.status_code)
        self.assertEqual(expected, result.body)
