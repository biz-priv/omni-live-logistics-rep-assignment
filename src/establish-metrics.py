import datetime
import dateutil.tz
import requests
import os
from shared.dynamo import put_item, get_table
# import pytz

def handler(event, context):
    list_of_users = ['bednchr','browaus','casajak','cruzale','elizmau','hodgbri','pilczac','ruizrob','schmric']

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

    # load_counter = {}
    # track_counter = {}
    # ontime_counter = {}
    # movements = {}

    # datetime.utcnow().replace(tzinfo=pytz.utc)
    # week_ago = datetime.datetime.today() - datetime.timedelta(days=7)

    week_ago = datetime.datetime.today() - datetime.timedelta(days=7)
    week_ago = week_ago.replace(tzinfo=dateutil.tz.gettz('US/Central'))

    for user in list_of_users:
        url = f"https://tms-lvlp.loadtracking.com/ws/api/movements/search?movement.dispatcher_user_id={user}&status=D&orderBy=destination.actual_arrival+DESC&recordLength=50"
        response = requests.get(url, auth=(username, password), headers=mcleod_headers)
        
        userData = {
            "user_id" : user,
            "load_counter": 0,
            "track_counter": 0,
            "ontime_counter": 0,
            "movements": []
        }
        
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
    
    print(userData)

    table_obj = get_table(os.environ["USER_METRICS_TABLE"]) 
    for userRecord in data:
        put_item(table_obj, userRecord)

    return "Function ran successfully"