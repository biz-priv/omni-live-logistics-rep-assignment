import datetime
import dateutil.tz
import requests
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.dynamo import put_item
from shared.api import searchMovementByUser, callins
from shared.user import getdata

import boto3
from boto3.dynamodb.types import TypeSerializer

ses = boto3.client('ses', region_name='us-east-1')

def handler(event, context):
    data=getdata()
    return data