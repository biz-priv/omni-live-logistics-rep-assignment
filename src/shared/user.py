
import os
import boto3
import datetime
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

def get_all_users():
    users = []
    table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])
    scan_kwargs = {}
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            users.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
    except Exception as err:
        print("Exception in scaning users")
        raise

    return users

def get_qualified_users():
    users = []
    table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])
    scan_kwargs = {
        'FilterExpression': "#qualified = :qualified",
        'ExpressionAttributeValues': {
            ':qualified' : "true" 
        },
        'ExpressionAttributeNames': {
            '#qualified' : 'qualified'
        }
    }
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            users.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
    except Exception as err:
        print("Exception in scaning users")
        raise

    return users


def query_users_for_weekday(weekday):
    users = []
    table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])
    scan_kwargs = {
        'FilterExpression': "contains(#days, :weekday)",
        'ExpressionAttributeValues': {
            ':weekday' : weekday
        },
        'ExpressionAttributeNames': {
            '#days' : 'days'
        },
    }
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            users.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
    except Exception as err:
        print("Exception in scaning users")
        raise

    return users

def update_last_used_timestamp(user):
    user["last_used"] = datetime.datetime.now()
    dynamodb_client.put_item(TableName=os.environ['USER_METRICS_TABLE'], Item=user)


def sort_users_by_last_used(users):
    sorted_users = sorted(users, key=lambda user: (not user.get("last_used", ""), user.get("last_used", "")))
    return sorted_users