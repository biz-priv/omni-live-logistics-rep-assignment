"""
* File: src\getdata.py
* Project: Omni-live-logistics-rep-assignment
* Author: Bizcloud Experts
* Date: 2023-12-14
* Confidential and Proprietary
"""
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