import datetime
import requests

def handler(event, context):
    find_parade_loads()
    return "Function ran successfully"

def find_parade_loads():
    username = "apiuser"
    password = "lvlpapiuser"
    mcleod_headers = {'Accept': 'application/json',
                      'Content-Type': 'application/json'}

    url = "https://tms-lvlp.loadtracking.com/ws/api/movements/search?dispatcher_user_id=parade&status=<>V"
    response = requests.get(url, auth=(username, password), headers=mcleod_headers)
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



def update_dispatcher(movement_id, new_user):
    # username = "apiuser"
    # password = "lvlpapiuser"
    # mcleod_headers = {'Accept': 'application/json',
    #                   'Content-Type': 'application/json'}

    # url = f"https://tms-lvlp.loadtracking.com/ws/movement/{movement_id}"
    # response = requests.get(url, auth=(username, password), headers=mcleod_headers)
    # output = response.json()
    # output['dispatcher_user_id'] = f"{new_user}"

    # put_url = "https://tms-lvlp.loadtracking.com/ws/movement/update"
    # put_response = requests.put(put_url, auth=(username, password), headers=mcleod_headers,json=output)
    # print(put_response.status_code)
    print("apis called")