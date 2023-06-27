"""Data access object for indexing settings"""
from __future__ import annotations


class DaoDynamoDB:
    """Class that implements loading from and saving to dynamodb"""

    def save(self, db_table):
        """Save the object to the dynamodb database"""
        db_table.put_item(Item=self._to_ddb_json())

    @staticmethod
    def save_list(db_table, objects: list[DaoDynamoDB]):
        with db_table.batch_writer() as batch:
            for object in objects:
                batch.put_item(Item=object._to_ddb_json())

    def _to_ddb_json(self):
        """Convert the current object to a JSON for storing in dynamodb"""
        raise NotImplementedError("Method form converting object to DynamoDB JSON not implemented")

    @classmethod
    def _from_ddb_json(cls, data):
        """Parse the JSON from dynamodb and create the object"""
        raise NotImplementedError("Method form converting DynamoDB JSON to object not implemented")

    @classmethod
    def load_key(
        cls,
        db_table,
        primary: str,
        secondary: int,
    ):
        """Retrieve a single object from the database"""
        response = db_table.get_item(Key={"primary": primary, "secondary": secondary})

        if "Item" in response:
            return cls._from_ddb_json(response["Item"])

    @staticmethod
    def query_condition(
        db_table,
        condition,
    ) -> list[dict]:
        """Query all objects in the database"""
        response = db_table.query(
            Select="ALL_ATTRIBUTES",
            KeyConditionExpression=condition,
        )
        return response.get("Items", [])
