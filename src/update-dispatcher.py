import os
import sys
import boto3

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.api import searchParadeLoads, getMovementById, updateMovement
from shared.user import get_qualified_users

ses = boto3.client('ses', region_name='us-east-1')

def handler(event, context):
    users = get_qualified_users()
    print(users)
    find_parade_loads(users)
    return "Function ran successfully"

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
                    update_dispatcher(output[move]['id'], users[index]["user_id"])
                    sendMailToUser( users[index]["user_id"], output[move]['id'] )
                    index = index+1
            else:
                print('There is one load')
                update_dispatcher(output['id'], users[index]["user_id"])
                sendMailToUser(users[index]["user_id"], output['id'] )
                index = index+1
    except Exception as error:
        print(error)
        return "Error - update_dispatcher"


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

def sendMailToUser( email, moveId ):

    with open(os.getcwd() + '/src/shared/res/assignment_notification.html', 'r', encoding='utf-8') as file:
    # Read the contents of the file into a string
        html_string = file.read()

    html_string = html_string.replace("{{ order_id }}", moveId)

    response = ses.send_email(
        Destination={
            'ToAddresses': [
                email
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
                'Data': f"Assigned Parade Order {moveId}",
                'Charset': "UTF-8",
            },
        },
        Source="noreply@omnilogistics.com"
    )