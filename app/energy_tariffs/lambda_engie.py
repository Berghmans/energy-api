"""Lambda handler for the Engie feeder"""
import os

import boto3

from engie import EngieIndexingSetting, GAS_URL, ENERGY_URL


def get_index_values() -> list[EngieIndexingSetting]:
    """Get the list of values"""
    return EngieIndexingSetting.from_url(GAS_URL) + EngieIndexingSetting.from_url(ENERGY_URL)


def handler(_event, _context):
    """The handler"""
    index_values = get_index_values()
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    EngieIndexingSetting.save_list(db_table, index_values)
