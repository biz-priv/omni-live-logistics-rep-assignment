# """
# * File: src/shared/dynamo.py
# * Project: Omni-live-logistics-rep-assignment
# * Author: Bizcloud Experts
# * Date: 2024-02-19
# * Confidential and Proprietary
# """
import boto3

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

def put_item(tableName, item):
    response = dynamodb.put_item(TableName=tableName, Item=item)
    # print("PutItem succeeded:", response)