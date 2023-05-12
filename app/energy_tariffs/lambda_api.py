import json
import os

import boto3

from api import Api, ApiResult


def handler(event, _context):
    """The handler"""
    print(json.dumps(event))
    dynamodb = boto3.resource("dynamodb")
    db_table = dynamodb.Table(os.environ["TABLE_NAME"])
    api = Api(db_table)
    method = api.parse(event)

    if method is not None:
        # Process the messages when we could parse it
        result = method.process()
        return result.to_api()

    return ApiResult(400)