
import os
import boto3
from datetime import datetime
from boto3.dynamodb.types import TypeSerializer

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

def getdata():
    table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])

    try:
        # Scan the DynamoDB table to retrieve all items
        response = table.scan()

        # Check if there are items
        items = response.get('Items', [])
        if items:
            for item in items:
                del item['movements']
                del item['days']
                item['tracking']=int((item['track_counter']/item['load_counter'])*100)
                item['ontime']=int((item['ontime_counter']/item["num_stops"])*100)
                del item['email']
                del item['manager_email']
                item["check"]= True if( (int((item['track_counter']/item['load_counter'])*100))>=80 and  (int((item['ontime_counter']/item['load_counter'])*100))>=90) else False
            return(items)
        else:
            print("No data found in the table")
            return None

    except Exception as err:
        print(f"Exception in getting data: {err}")
        raise


def update_toggle_for_user(user_id, inOffice):
    table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])

    try:
        # Update the DynamoDB item
        table.update_item(
            Key={
                'user_id': user_id
            },
            UpdateExpression='SET inOffice = :inOffice',
            ExpressionAttributeValues={
                ':inOffice': inOffice
            }
        )

        print(f"Toggle updated for user {user_id}. New toggle value: {inOffice}")
        return True

    except Exception as err:
        print(f"Exception in updating toggle for user {user_id}: {err}")
        raise

def update_office_status(user):
    try:
        today = datetime.now().strftime('%A')
        is_working_day = today in user['days']

        # Update inOffice based on the working days
        if is_working_day:
            new_inOffice_value = 'yes'
        else:
            new_inOffice_value = 'no'
        return new_inOffice_value
    except Exception as err:
        print(f"Exception in updating inOffice for working users: {err}")
        raise

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
        'FilterExpression': "#qualified = :qualified AND #inOffice = :inOffice",
        'ExpressionAttributeValues': {
            ':qualified': "true",
            ':inOffice': "yes"  # Adjust based on the actual values in your 'inOffice' column
        },
        'ExpressionAttributeNames': {
            '#qualified': 'qualified',
            '#inOffice': 'inOffice'
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
    user["last_used"] = datetime.now().isoformat()
    serializer = TypeSerializer()
    dyn_item = {key: serializer.serialize(value) for key, value in user.items()}
    dynamodb_client.put_item(TableName=os.environ['USER_METRICS_TABLE'], Item=dyn_item)

def sort_users_by_last_used(users):
    def custom_sort_key(user):
        last_used = user.get("last_used")
        if not last_used:
            return (0, datetime.min)
        return (1, datetime.fromisoformat(last_used))
    sorted_users = sorted(users, key=custom_sort_key)
    return sorted_users