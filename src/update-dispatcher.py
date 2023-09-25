import datetime
import requests
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.api import searchParadeLoads, getMovementById, updateMovement
from shared.user import get_qualified_users

def handler(event, context):
    users = get_qualified_users()
    print(users)
    find_parade_loads(users)
    return "Function ran successfully"

def find_parade_loads(users):
    try:
        response = searchParadeLoads()
        output = response.json()
        index = 0
        if output is None:
            print('No new parade loads')
        else:
            if isinstance(output, list):
                print('There are multiple loads')
                for move in range(len(output)):
                    update_dispatcher(output[move]['id'], users[index]["user_id"])
                    index = index+1
            else:
                print('There is one load')
                update_dispatcher(output['id'], users[index]["user_id"])
                index = index+1
    except Exception as error:
        print(error)
        return "Error - update_dispatcher"


def update_dispatcher(movement_id, new_user):
    try:
        response = getMovementById(movement_id)
        output = response.json()
        output['dispatcher_user_id'] = f"{new_user}"

        print(output)

        put_response = updateMovement(output)
        print(put_response.status_code)
        # print("apis called")
    except Exception as error:
        print(f"Error in updating dispatcher, movement_id - {movement_id}, new_user - {new_user}")
        print(error)
        raise
    
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