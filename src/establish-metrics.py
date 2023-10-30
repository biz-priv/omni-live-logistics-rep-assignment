import datetime
import dateutil.tz
import requests
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.dynamo import put_item
from shared.api import searchMovementByUser, callins
from shared.user import get_all_users

import boto3
from boto3.dynamodb.types import TypeSerializer

ses = boto3.client('ses', region_name='us-east-1')

def handler(event, context):

    try:
        #get all users from dynamodb
        list_of_users = get_all_users()

        #determine timestamps
        now = datetime.datetime.utcnow()
        yesterday = now - datetime.timedelta(days = 1)

        #convert timestamps into mcleod-friendly timestamps
        now = now.strftime('%Y%m%d%H%M%S%z') + '-0000'
        yesterday = yesterday.strftime('%Y%m%d%H%M%S%z') + '-0000'
        yesterday = datetime.datetime.strptime(yesterday, '%Y%m%d%H%M%S%z')

        data = []

        week_ago = datetime.datetime.today() - datetime.timedelta(days=7)
        week_ago = week_ago.replace(tzinfo=dateutil.tz.gettz('US/Central'))

        for user in list_of_users:
            response = searchMovementByUser(user["user_id"])
            
            if response.status_code < 200 and response.status_code >= 300:
                print(f"Error encountered in searchMovementByUser, user_id - {user['user_id']}, response - {response.json()}")
                continue

            userData = user.copy()
            userData["load_counter"] = 0
            userData["track_counter"] = 0
            userData["ontime_counter"] = 0
            userData["movements"] = []
            userData["qualified"] = "false"
            
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
                    callin_response = callins(output[move]['id'])

                    if ( callin_response.status_code < 200 and callin_response.status_code >= 300 ):
                        print(f"Error encountered in callin_response, move_id - {output[move]['id']}, response - {callin_response.json()}")
                        continue

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
                    userData["qualified"]="true"
        

        serializer = TypeSerializer()

        for userRecord in data:
            try:
                dyn_item = {key: serializer.serialize(value) for key, value in userRecord.items()}
                print(dyn_item)
                put_item(os.environ["USER_METRICS_TABLE"], dyn_item)
            except Exception as e:
                print(F"Error while saving record to dyanmo, error - {e} ,record - {userRecord}")

        sendMail(data)

        return "Function ran successfully"
    except Exception as error:
        Info=f"The Lambda Function establish-metrics failed with error - {error}"
        response = ses.send_email(
            Source="noreply@omnilogistics.com",
            Destination={
                'ToAddresses': ['support@bizcloudexperts.com']
            },
            Message={
                'Body': {
                    'Text': {
                        'Data': Info
                    }
                },
                'Subject': {
                    'Data': f"The Lambda Function establish-metrics failed with error - {error} \n This Lambda is part of omni-rep-assignment",
                    'Charset': "UTF-8"
                },
            },
        )
        print("Error - ",error)
        raise 

def sendMail( data ):

    qualified_users = [f"""<div
            style="font-family: inherit; text-align: inherit">
            {user["user_id"]}</div>""" for user in data if user["qualified"] ]
            

    with open(os.getcwd() + '/src/shared/res/morning_email.html', 'r', encoding='utf-8') as file:
    # Read the contents of the file into a string
        html_string = file.read()

    html_string = html_string.replace("{{user-list}}", "".join(qualified_users))

    response = ses.send_email(
        Destination={
            'ToAddresses': [
                "raviteja.kalluri@bizcloudexperts.com",
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