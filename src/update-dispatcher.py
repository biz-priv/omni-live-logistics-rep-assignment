import os
import sys
from datetime import datetime
import boto3

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.api import searchParadeLoads, getMovementById, updateMovement
from shared.user import get_qualified_users, update_last_used_timestamp, sort_users_by_last_used
# from shared.dynamo import put_item

ses = boto3.client('ses', region_name='us-east-1')
def handler(event, context):
    try:
        users=get_qualified_users()
        sorted_users = sort_users_by_last_used(users)
        print(sorted_users)
        find_parade_loads(sorted_users)
        return "Function ran successfully"
    except Exception as error:
        Info=f"The Lambda Function failed with error - {error}"
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
                    'Data': "Lamba Failed",
                    'Charset': "UTF-8"
                },
            },
        )
        print("Error - ",error)
        raise

def find_parade_loads(users):
    try:
        response = searchParadeLoads()
        output = response.json()
        index = 0
        if output is None:
            print('No new parade loads')
        else:
            if isinstance(output, list):
                print('There are multiple loads')
                for move in range(len(output)):
                    print(f"User Id - {users[index]['user_id']}")
                    update_dispatcher(output[move]['id'], users[index]["user_id"])
                    sendMailToUser( [users[index]["email"]], [users[index]["manager_email"]] , output[move]['id'] )
                    update_last_used_timestamp(users[index])
                    index = index+1
            else:
                print('There is one load')
                print(f"User Id - {users[index]['user_id']}")
                update_dispatcher(output['id'], users[index]["user_id"])
                sendMailToUser([users[index]["email"]], [users[index]["manager_email"]], output['id'] )
                update_last_used_timestamp(users[index])
                index = index+1
    except Exception as error:
        print("Error - ",error)
        #return "Error - update_dispatcher"
        raise

def update_dispatcher(movement_id, new_user):
    try:
        response = getMovementById(movement_id)
        output = response.json()
        output['dispatcher_user_id'] = f"{new_user}"

        print(output)

        put_response = updateMovement(output)
        print(put_response.status_code)
        # print("apis called")
    except Exception as error:
        print(f"Error in updating dispatcher, movement_id - {movement_id}, new_user - {new_user}")
        print(error)
        raise

def sendMailToUser( emails, ccemails,  moveId ):

    with open(os.getcwd() + '/src/shared/res/assignment_notification.html', 'r', encoding='utf-8') as file:
    # Read the contents of the file into a string
        html_string = file.read()

    html_string = html_string.replace("{{ order_id }}", moveId)

    ses.send_email(
        Destination={
            'ToAddresses': emails,
            'CcAddresses': ccemails
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': "UTF-8",
                    'Data': html_string,
                }
            },
            'Subject': {
                # 'Data': f"Test",
                'Data': f"Assigned Parade Order {moveId}",
                'Charset': "UTF-8",
            },
        },
        Source="noreply@omnilogistics.com"
    )
