import json
import os
import logging

import boto3

from api import Api
from api.result import ApiResult


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, _context):
    """The handler"""
    logger.info(json.dumps(event))
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    base_path = os.environ["API_BASE_PATH"]
    api = Api(base_path, db_table)
    method = api.parse(event)

    if method is not None:
        # Process the messages when we could parse it
        logger.info(f"Processing the event using the {method.__class__.__name__} method")
        result = method.process()
        logger.info(f"Returning {json.dumps(result.to_api())}")
        return result.to_api()

    logger.warning("Returning Bad Request as we were not able to find a suitable processing method")
    return ApiResult(400).to_api()
