import datetime
import requests
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from .shared.api import searchParadeLoads, getMovementById, updateMovement

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