"""Module that contains several creator functions for the unit tests"""
import boto3


def create_dynamodb_table():
    """Create the dynamodb table"""
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.create_table(
        TableName="singular-table",
        AttributeDefinitions=[
            {"AttributeName": "primary", "AttributeType": "S"},
            {"AttributeName": "secondary", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "primary", "KeyType": "HASH"},
            {"AttributeName": "secondary", "KeyType": "RANGE"},
        ],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        TableClass="STANDARD",
    )
