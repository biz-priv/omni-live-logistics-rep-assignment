import requests

username = "apiuser"
password = "lvlpapiuser"
mcleod_headers = {'Accept': 'application/json',
                'Content-Type': 'application/json'}
base_url = "https://tms-lvlp.loadtracking.com/ws"

def searchMovementByUser(user_id):
    url = f"{base_url}/api/movements/search?movement.dispatcher_user_id={user_id}&status=D&orderBy=destination.actual_arrival+DESC&recordLength=50"
    response = requests.get(url, auth=(username, password), headers=mcleod_headers)
    return response

def callins(move_id):
    url = f"https://tms-lvlp.loadtracking.com/ws/api/callins/M/{move_id}"
    response = requests.get(url, auth=(username, password), headers=mcleod_headers)
    return response
        
def searchParadeLoads():
    url = f"{base_url}/api/movements/search?dispatcher_user_id=parade&status=<>V"
    response = requests.get(url, auth=(username, password), headers=mcleod_headers)
    return response

def getMovementById(movement_id):
    url = f"{base_url}/movement/{movement_id}"
    response = requests.get(url, auth=(username, password), headers=mcleod_headers)
    return response

def updateMovement(json):
    url = f"{base_url}/movement/update"
    response = requests.put(url, auth=(username, password), headers=mcleod_headers,json=json)
    return response