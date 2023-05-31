"""Test module for IndexingSetting DAO"""
from __future__ import annotations
from unittest import TestCase
from datetime import datetime, timedelta

from moto import mock_dynamodb
from pytz import utc

from dao import IndexingSetting, IndexingSettingTimeframe, IndexingSettingOrigin, IndexingSettingDocumentation, DaoDynamoDB
from tests.creators import create_dynamodb_table


@mock_dynamodb
class TestIndexingSetting(TestCase):
    """Test class for IndexingSetting"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.index_name = "index1"
        self.index_timeframe = IndexingSettingTimeframe.HOURLY
        self.index_datetime = datetime(2023, 5, 12, 5, 0, 0, tzinfo=utc)
        self.index_datetime_str = "2023-05-12 05:00:00"
        self.index_source = "src"
        self.index_origin = IndexingSettingOrigin.ORIGINAL
        self.index_value = 1.1
        self.index_obj = IndexingSetting(
            self.index_name,
            self.index_value,
            self.index_timeframe,
            self.index_datetime,
            self.index_source,
            self.index_origin,
        )

    def test_save(self):
        """Test the save method"""
        self.index_obj.save(self.db_table)
        response = self.db_table.get_item(
            Key={
                "primary": f"{self.index_source}#ORIGINAL#HOURLY#{self.index_name}",
                "secondary": int(self.index_datetime.astimezone(utc).timestamp()),
            }
        )
        self.assertIn("Item", response)
        self.assertIn("primary", response["Item"])
        self.assertIn("secondary", response["Item"])
        self.assertIn("last_updated", response["Item"])
        self.assertEqual("1.1", response["Item"]["value"])

    def test_load(self):
        """Test the load method"""
        self.index_obj.save(self.db_table)
        obj2 = IndexingSetting.load(self.db_table, self.index_source, self.index_name, self.index_timeframe, self.index_datetime)
        self.assertEqual(self.index_obj.name, obj2.name)
        self.assertEqual(self.index_obj.value, obj2.value)
        self.assertEqual(self.index_obj.timeframe, obj2.timeframe)
        self.assertEqual(self.index_obj.date, obj2.date)
        self.assertEqual(self.index_obj.source, obj2.source)
        self.assertEqual(self.index_obj.origin, obj2.origin)

        # Test not existing
        self.assertIsNone(IndexingSetting.load(self.db_table, "unknown", self.index_name, self.index_timeframe, self.index_datetime))

    def test_save_list(self):
        """Test the save_list method"""
        obj2 = IndexingSetting(
            self.index_name,
            self.index_value,
            self.index_timeframe,
            self.index_datetime,
            "source2",
            self.index_origin,
        )
        IndexingSetting.save_list(self.db_table, [self.index_obj, obj2])
        self.assertIsNotNone(IndexingSetting.load(self.db_table, self.index_source, self.index_name, self.index_timeframe, self.index_datetime))
        self.assertIsNotNone(IndexingSetting.load(self.db_table, "source2", self.index_name, self.index_timeframe, self.index_datetime))

    def test_query(self):
        """Test the query method"""
        self.index_obj.save(self.db_table)
        IndexingSetting(
            self.index_name,
            self.index_value,
            IndexingSettingTimeframe.MONTHLY,
            self.index_datetime,
            self.index_source,
            self.index_origin,
        ).save(self.db_table)
        IndexingSetting(
            self.index_name,
            self.index_value,
            IndexingSettingTimeframe.MONTHLY,
            self.index_datetime + timedelta(days=1),
            self.index_source,
            self.index_origin,
        ).save(self.db_table)
        IndexingSetting(
            self.index_name,
            self.index_value,
            IndexingSettingTimeframe.MONTHLY,
            self.index_datetime,
            "source2",
            self.index_origin,
        ).save(self.db_table)
        objects = IndexingSetting.query(self.db_table, self.index_source, self.index_name)
        self.assertEqual(2, len(objects))

    def test_query_timeframe(self):
        """Test the query method"""
        for i in range(0, 5):
            IndexingSetting(
                self.index_name,
                self.index_value,
                self.index_timeframe,
                datetime(2023, 1 + i, 1, 0, 0, 0, tzinfo=utc),
                self.index_source,
                self.index_origin,
            ).save(self.db_table)
        objects = IndexingSetting.query(self.db_table, self.index_source, self.index_name, timeframe=self.index_timeframe)
        self.assertEqual(5, len(objects))
        threshold = datetime(2023, 3, 1, 0, 0, 0, tzinfo=utc)
        objects = IndexingSetting.query(self.db_table, self.index_source, self.index_name, timeframe=self.index_timeframe, start=threshold)
        self.assertEqual(3, len(objects))
        objects = IndexingSetting.query(self.db_table, self.index_source, self.index_name, timeframe=self.index_timeframe, end=threshold)
        self.assertEqual(2, len(objects))
        objects = IndexingSetting.query(self.db_table, self.index_source, self.index_name, timeframe=self.index_timeframe, start=threshold, end=threshold)
        self.assertEqual(1, len(objects))
        objects = IndexingSetting.query(
            self.db_table,
            self.index_source,
            self.index_name,
            timeframe=self.index_timeframe,
            start=datetime(2023, 2, 1, 0, 0, 0, tzinfo=utc),
            end=datetime(2023, 4, 1, 0, 0, 0, tzinfo=utc),
        )
        self.assertEqual(3, len(objects))


@mock_dynamodb
class TestIndexingSettingDocumentation(TestCase):
    """Test class for IndexingSetting"""

    def setUp(self):
        """Set up the test"""
        self.db_table = create_dynamodb_table()
        self.index_obj = IndexingSettingDocumentation(
            name="index1", timeframe=IndexingSettingTimeframe.HOURLY, source="src", origin=IndexingSettingOrigin.ORIGINAL
        )

    def test_save(self):
        """Test the save method"""
        self.index_obj.save(self.db_table)
        response = self.db_table.get_item(
            Key={
                "primary": "indexingsettingdoc",
                "secondary": hash(self.index_obj),
            }
        )
        self.assertIn("Item", response)
        self.assertIn("primary", response["Item"])
        self.assertIn("secondary", response["Item"])
        self.assertIn("last_updated", response["Item"])
        self.assertEqual("index1", response["Item"]["name"])

    def test_save_list(self):
        """Test the save_list method"""
        obj2 = IndexingSettingDocumentation(name="index1", timeframe=IndexingSettingTimeframe.HOURLY, source="src2", origin=IndexingSettingOrigin.ORIGINAL)
        IndexingSettingDocumentation.save_list(self.db_table, [self.index_obj, obj2])
        self.assertEqual(2, len(IndexingSettingDocumentation.query(self.db_table)))

    def test_query(self):
        """Test the query method"""
        self.index_obj.save(self.db_table)
        IndexingSettingDocumentation(name="index1", timeframe=IndexingSettingTimeframe.HOURLY, source="src2", origin=IndexingSettingOrigin.ORIGINAL).save(
            self.db_table
        )
        IndexingSettingDocumentation(name="index1", timeframe=IndexingSettingTimeframe.HOURLY, source="src2", origin=IndexingSettingOrigin.ORIGINAL).save(
            self.db_table
        )
        objects = IndexingSettingDocumentation.query(self.db_table)
        self.assertEqual(2, len(objects))


@mock_dynamodb
class TestDaoDynamoDB(TestCase):
    """Test class for DaoDynamoDB"""

    def test_not_implemented(self):
        """Test the methods to be implemented"""
        self.assertRaises(NotImplementedError, DaoDynamoDB._from_ddb_json, {})
        self.assertRaises(NotImplementedError, DaoDynamoDB()._to_ddb_json)
