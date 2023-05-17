"""Module for the feeder lambda handler"""
from datetime import datetime, timedelta
import os
import logging

import boto3
from pytz import utc

from feeders.engie import EngieIndexingSetting
from feeders.eex import EEXIndexingSetting
from feeders.entsoe import EntsoeIndexingSetting


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def engie_handler(event, _context):
    """The Engie handler"""
    if "start" in event:
        not_before = utc.localize(datetime.strptime(event["start"], "%Y/%m/%d"))
    else:
        not_before = datetime.now(utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=90)
    index_values = EngieIndexingSetting.get_gas_values(not_before) + EngieIndexingSetting.get_energy_values(not_before)
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EngieIndexingSetting.save_list(db_table, index_values)

    # Derived values
    calculation_date = None
    if "calculate" in event:
        calculation_date = utc.localize(datetime.strptime(event["calculate"], "%Y/%m/%d"))
    derived_values = EngieIndexingSetting.calculate_derived_values(db_table, calculation_date)
    logger.info(f"Sending {len(derived_values)} derived indexing settings to the database")
    EngieIndexingSetting.save_list(db_table, derived_values)


def eex_handler(event, _context):
    """The EEX handler"""
    if "start" in event and "end" in event:
        not_before = utc.localize(datetime.strptime(event["start"], "%Y/%m/%d")).date()
        not_after = utc.localize(datetime.strptime(event["end"], "%Y/%m/%d")).date()
    else:
        not_before = (datetime.now(utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)).date()
        not_after = None
    index_values = EEXIndexingSetting.get_ztp_values(date_filter=not_before, end=not_after)
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EEXIndexingSetting.save_list(db_table, index_values)


def entsoe_handler(event, _context):
    """The ENTSO-E handler"""
    if "start" in event and "end" in event:
        not_before = utc.localize(datetime.strptime(event["start"], "%Y/%m/%d"))
        not_after = utc.localize(datetime.strptime(event["end"], "%Y/%m/%d"))
    else:
        now = datetime.now(utc).replace(hour=0, minute=0, second=0, microsecond=0)
        not_before = now - timedelta(days=7)
        not_after = now + timedelta(days=1)
    logger.info(f"Fetching values from {not_before} to {not_after}")
    api_key = EntsoeIndexingSetting.fetch_api_key(os.environ["SECRET_ARN"])
    index_values = EntsoeIndexingSetting.get_be_values(api_key=api_key, start=not_before, end=not_after)
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    logger.info(f"Sending {len(index_values)} indexing settings to the database")
    EntsoeIndexingSetting.save_list(db_table, index_values)


def handler(event, context):
    """The handler"""
    if "feed" in event:
        feeder = event["feed"]
        logger.info(f"Initiating {feeder} handler")
        if feeder == "engie":
            engie_handler(event, context)
        if feeder == "eex":
            eex_handler(event, context)
        if feeder == "entsoe":
            entsoe_handler(event, context)
    else:
        logger.info("No feed defined, so skipping...")
