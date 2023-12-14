import datetime
import dateutil.tz
import requests
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.dynamo import put_item
from shared.api import searchMovementByUser, callins
from shared.user import get_all_users,update_toggle_for_user

import boto3
from boto3.dynamodb.types import TypeSerializer

ses = boto3.client('ses', region_name='us-east-1')

def handler(event, context):
    print("Event :",event)
    user_id=event['body']['user_id']
    inOffice_status=event['body']['toggle']
    update=update_toggle_for_user(user_id,inOffice_status)
    return update
