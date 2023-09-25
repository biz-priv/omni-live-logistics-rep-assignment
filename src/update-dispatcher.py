import datetime
import requests
import os
import sys
from boto3.dynamodb.conditions import Key, Attr

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.api import searchParadeLoads, getMovementById, updateMovement

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def handler(event, context):
    find_parade_loads()
    return "Function ran successfully"

def find_parade_loads():
    try:
        response = searchParadeLoads()
        output = response.json()
        if output is None:
            print('No new parade loads')
        else:
            if isinstance(output, list):
                print('There are multiple loads')
                for move in range(len(output)):
                    update_dispatcher(output[move]['id'], 'schndre')
            else:
                print('There is one load')
                update_dispatcher(output['id'], 'schndre')
    except Exception as error:
        print(error)
        return "Error - update_dispatcher"


def update_dispatcher(movement_id, new_user):
    try:
        # response = getMovementById(movement_id)
        # output = response.json()
        # output['dispatcher_user_id'] = f"{new_user}"

        # put_response = updateMovement(output)
        # print(put_response.status_code)
        print("apis called")
    except Exception as error:
        print(error)
        return "Error - update_dispatcher"
    
def scan_users():
    users = []
    table = dynamodb.Table(os.environ('USER_METRICS_TABLE'))
    scan_kwargs = {
        'FilterExpression': Attr('qualified').eq('true')
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