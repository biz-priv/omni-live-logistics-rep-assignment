# """
# * File: src/shared/api.py
# * Project: Omni-live-logistics-rep-assignment
# * Author: Bizcloud Experts
# * Date: 2024-02-19
# * Confidential and Proprietary
# """
import requests
import os

base_url = os.environ["API_URL"]
username = os.environ["API_USERNAME"]
password = os.environ["API_PASSWORD"]
mcleod_headers = {'Accept': 'application/json',
                'Content-Type': 'application/json'}

def searchMovementByUser(user_id):
    try:
        url = f"{base_url}/api/movements/search?movement.dispatcher_user_id={user_id}&status=D&orderBy=destination.actual_arrival+DESC&recordLength=300"
        response = requests.get(url, auth=(username, password), headers=mcleod_headers)
        return response
    except Exception as error:
        print(f"Error at searchMovementByUser, user_id - {user_id}")
        raise

def callins(move_id):
    try:
        url = f"https://tms-lvlp.loadtracking.com/ws/api/callins/M/{move_id}"
        response = requests.get(url, auth=(username, password), headers=mcleod_headers)
        return response
    except Exception as error:
        print(f"Error at callins, move_id - {move_id}")
        raise
        
def searchParadeLoads():
    try:
        url = f"{base_url}/api/movements/search?dispatcher_user_id=parade&status=<>V"
        response = requests.get(url, auth=(username, password), headers=mcleod_headers)
        return response
    except Exception as error:
        print(f"Error at searchParadeLoads")
        raise

def getMovementById(movement_id):
    try:
        url = f"{base_url}/movement/{movement_id}"
        response = requests.get(url, auth=(username, password), headers=mcleod_headers)
        return response
    except Exception as error:
        print(f"Error at getMovementById, movement_id - {movement_id}")
        raise

def updateMovement(json):
    try:    
        url = f"{base_url}/movement/update"
        response = requests.put(url, auth=(username, password), headers=mcleod_headers,json=json)
        return response
    except Exception as error:
        print(f"Error at updateMovement, json - {json}")
        raise