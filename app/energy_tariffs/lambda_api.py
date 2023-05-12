import json
import os
import logging

import boto3

from api import Api, ApiResult


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, _context):
    """The handler"""
    print(json.dumps(event))
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    base_path = os.environ["API_BASE_PATH"]
    api = Api(base_path, db_table)
    method = api.parse(event)

    if method is not None:
        # Process the messages when we could parse it
        result = method.process()
        logger.info(f"Returning {json.dumps(result.to_api())}")
        return result.to_api()

    return ApiResult(400).to_api()
