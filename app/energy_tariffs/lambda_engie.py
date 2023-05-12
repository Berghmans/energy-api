"""Lambda handler for the Engie feeder"""
import os
import logging

import boto3

from engie import EngieIndexingSetting, GAS_URL, ENERGY_URL


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_index_values() -> list[EngieIndexingSetting]:
    """Get the list of values"""
    return EngieIndexingSetting.from_url(GAS_URL) + EngieIndexingSetting.from_url(ENERGY_URL)


def handler(_event, _context):
    """The handler"""
    index_values = get_index_values()
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EngieIndexingSetting.save_list(db_table, index_values)
