import boto3

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

def put_item(tableName, item):
    response = dynamodb.put_item(TableName=tableName, Item=item)
    print("PutItem succeeded:", response)