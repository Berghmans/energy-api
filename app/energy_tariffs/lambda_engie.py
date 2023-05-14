"""Lambda handler for the Engie feeder"""
from datetime import datetime, timedelta
import os
import logging

import boto3


from feeders.engie import EngieIndexingSetting


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(_event, _context):
    """The handler"""
    not_before = datetime.now() - timedelta(days=90)
    index_values = EngieIndexingSetting.get_gas_values(not_before) + EngieIndexingSetting.get_energy_values(not_before)
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EngieIndexingSetting.save_list(db_table, index_values)
