"""Lambda handler for the EEX feeder"""
from datetime import datetime, date, timedelta
import os
import logging

import boto3

from feeders.eex import EEXIndexingSetting


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, _context):
    """The handler"""
    if "start" in event and "end" in event:
        not_before = datetime.strptime(event["start"], "%Y/%m/%d").date()
        not_after = datetime.strptime(event["end"], "%Y/%m/%d").date()
    else:
        not_before = date.today() - timedelta(days=7)
        not_after = None
    index_values = EEXIndexingSetting.get_ztp_values(date_filter=not_before, end=not_after)
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EEXIndexingSetting.save_list(db_table, index_values)
