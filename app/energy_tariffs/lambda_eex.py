"""Lambda handler for the EEX feeder"""
from datetime import date, timedelta
import os
import logging

import boto3

from feeders.eex import EEXIndexingSetting


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(_event, _context):
    """The handler"""
    not_before = date.today() - timedelta(days=7)
    index_values = EEXIndexingSetting.get_ztp_values(not_before)
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EEXIndexingSetting.save_list(db_table, index_values)
