import datetime
import dateutil.tz
import requests
import os
from .shared.dynamo import put_item
# import pytz

import boto3
from boto3.dynamodb.types import TypeSerializer

dynamodb = boto3.client('dynamodb', region_name='us-east-1')
ses = boto3.client('ses', region_name='us-east-1')

def handler(event, context):
    list_of_users = {"bednchr": "cbednarski@omnilogistics.com",
                  "browaus": "abrown@omnilogistics.com",
                  "casajak": "jcasati@omnilogistics.com",
                  "cruzale": "alcruz@omnilogistics.com",
                  "elizmau": "melizalde@omnilogistics.com",
                  "hodgbri": "bhodge@omnilogistics.com",
                  "pilczac": "zpilcher@omnilogistics.com",
                  "ruizrob": "rruiz@omnilogistics.com",
                  "schmric": "rschmidt@omnilogistics.com"
    }

    #determine timestamps
    now = datetime.datetime.utcnow()
    yesterday = now - datetime.timedelta(days = 1)

    #convert timestamps into mcleod-friendly timestamps
    now = now.strftime('%Y%m%d%H%M%S%z') + '-0000'
    yesterday = yesterday.strftime('%Y%m%d%H%M%S%z') + '-0000'
    yesterday = datetime.datetime.strptime(yesterday, '%Y%m%d%H%M%S%z')


    username = "apiuser"
    password = "lvlpapiuser"
    mcleod_headers = {'Accept': 'application/json',
                      'Content-Type': 'application/json'}

    data = []

    week_ago = datetime.datetime.today() - datetime.timedelta(days=7)
    week_ago = week_ago.replace(tzinfo=dateutil.tz.gettz('US/Central'))

    for user_id, email in list_of_users.items():
        url = f"https://tms-lvlp.loadtracking.com/ws/api/movements/search?movement.dispatcher_user_id={user_id}&status=D&orderBy=destination.actual_arrival+DESC&recordLength=50"
        response = requests.get(url, auth=(username, password), headers=mcleod_headers)
        
        userData = {
            "user_id" : user_id,
            "email" : email,
            "load_counter": 0,
            "track_counter": 0,
            "ontime_counter": 0,
            "movements": [],
            "qualified": False
        }
        data.append(userData)
        
        output = response.json()
        for move in range(len(output)):
            num_of_stops = len(output[move]['stops'])

            #determine when the load actually delivered
            for stop in range(len(output[move]['stops'])):
                if output[move]['stops'][stop]['movement_sequence'] == num_of_stops:
                    try:
                        appt_time = output[move]['stops'][stop]['sched_arrive_late']
                    except:
                        appt_time = output[move]['stops'][stop]['sched_arrive_early']
                    appt_time = datetime.datetime.strptime(appt_time, '%Y%m%d%H%M%S%z')
                    actual_arrival = datetime.datetime.strptime(output[move]['stops'][stop]['actual_arrival'], '%Y%m%d%H%M%S%z')

            if actual_arrival > week_ago:
                # add load to load_counter and to the movement record
                userData["load_counter"] = userData["load_counter"] + 1
                userData["movements"].append(output[move]['id'])

                #use data previously gathered to determine if the load was delivered ontime
                if actual_arrival <= appt_time:
                    userData["ontime_counter"] = userData["ontime_counter"] + 1

                # get callins to determine if the load tracked
                callin_url = f"https://tms-lvlp.loadtracking.com/ws/api/callins/M/{output[move]['id']}"
                callin_response = requests.get(callin_url, auth=(username, password), headers=mcleod_headers)
                callin_output = callin_response.json()
                lat = 0
                long = 0
                for callin in range(len(callin_output)):
                    try:
                        lat = callin_output[callin]['latitude']
                        long = callin_output[callin]['longitude']
                    except:
                        pass
                if lat != 0 and long != 0:
                    userData["track_counter"] = userData["track_counter"] + 1
            else:
                pass

            if userData["track_counter"] / userData["load_counter"] > 0.8 and userData["ontime_counter"] /  userData["load_counter"] > 0.9:
                userData["qualified"]=True
    
    print(data)

    serializer = TypeSerializer()

    for userRecord in data:
        dyn_item = {key: serializer.serialize(value) for key, value in userRecord.items()}
        print(dyn_item)
        put_item(os.environ["USER_METRICS_TABLE"], dyn_item)

    sendMail(data)

    return "Function ran successfully"

def sendMail( data ):

    qualified_users = [f"""<div
            style="font-family: inherit; text-align: inherit">
            {user["user_id"]}</div>""" for user in data if user["qualified"] ]
            

    with open(os.getcwd() + '/src/shared/res/morning_email.html', 'r', encoding='utf-8') as file:
    # Read the contents of the file into a string
        html_string = file.read()

    print("".join(qualified_users))
    html_string = html_string.replace("{{user-list}}", "".join(qualified_users));

    response = ses.send_email(
        Destination={
            'ToAddresses': [
                "abhishek@bizcloudexperts.com",
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': "UTF-8",
                    'Data': html_string,
                }
            },
            'Subject': {
                'Data': "Parade Assignment Qualified Users",
                'Charset': "UTF-8",
            },
        },
        Source="noreply@omnilogistics.com"
    )