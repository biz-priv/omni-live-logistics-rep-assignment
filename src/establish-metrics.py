import os
import sys
import time
import boto3
from boto3.dynamodb.types import TypeSerializer

sys.path.append(os.path.join(os.path.dirname(__file__)))

from shared.dynamo import put_item 
from shared.user import get_all_users, update_office_status

ses = boto3.client('ses', region_name='us-east-1')
athena_client = boto3.client('athena')

def handler(event, context):
    try:
        list_of_users = get_all_users()
        data = []

        for user in list_of_users:
            user_id = user["user_id"]
            movements = query_movements_by_user(user_id)

            userData = user.copy()
            userData["load_counter"] = 0
            userData["track_counter"] = 0
            userData["ontime_counter"] = 0
            userData["movements"] = []
            userData["qualified"] = "false"
            userData["inOffice"] = update_office_status(user)

            if movements:
                userData["movements"] = [m['id'] for m in movements]
                userData["load_counter"] = len(movements)

                tracked_info = query_tracking_info(userData["movements"])
                userData["track_counter"] = tracked_info['num_tracked']

                ontime_info = query_ontime_info(userData["movements"])
                userData["ontime_counter"] = ontime_info['num_on_time_stops']
                userData["num_stops"]=ontime_info['num_stops']

                if userData["load_counter"] > 0:
                    if (int(userData["track_counter"]) / int(userData["load_counter"]) >= 0.8 and 
                        int(userData["ontime_counter"]) / int(userData["num_stops"]) >= 0.9):
                        userData["qualified"] = "true"

            data.append(userData)

        serializer = TypeSerializer()
        for userRecord in data:
            try:
                dyn_item = {key: serializer.serialize(value) for key, value in userRecord.items()}
                put_item(os.environ["USER_METRICS_TABLE"], dyn_item)
            except Exception as e:
                print(f"Error while saving record to dynamo, error - {e}, record - {userRecord}")

        return "Function ran successfully"

    except Exception as error:
        info = f"The Lambda Function establish-metrics failed with error - {error}"
        response = ses.send_email(
            Source="noreply@omnilogistics.com",
            Destination={'ToAddresses': ['support@bizcloudexperts.com']},
            Message={
                'Body': {'Text': {'Data': info}},
                'Subject': {'Data': f"OMNI - Rep-Assignment \n The Lambda Function update-dispatcher failed with error - {error}", 'Charset': "UTF-8"}
            },
        )
        print("Error - ", error)
        raise

def query_movements_by_user(user_id):
    query = f"""
    WITH w1 AS (
        SELECT MAX(m.transact_id) AS transact_id, m.id
        FROM movement m
        GROUP BY m.id
    ),
    w2 AS (
        SELECT MAX(s.transact_id) AS transact_id, s.id
        FROM stop s
        GROUP BY s.id
    )
    SELECT DISTINCT m.id
    FROM (SELECT m.* FROM movement m JOIN w1 ON m.id = w1.id AND m.transact_id = w1.transact_id) m
    JOIN (SELECT s.* FROM stop s JOIN w2 ON s.id = w2.id AND s.transact_id = w2.transact_id) s2 ON s2.id = m.dest_stop_id
    WHERE m.dispatcher_user_id = '{user_id}'
    AND CAST(s2.actual_arrival AS date) >= DATE_ADD('day', -14, CURRENT_DATE)
    AND UPPER(m.status) = 'D'
    """
    return execute_athena_query(query)

def query_tracking_info(movement_ids):
    movement_ids_str = ','.join(f"'{m}'" for m in movement_ids)
    query = f"""
    WITH w1 AS (
        SELECT MAX(m.transact_id) AS transact_id, m.id
        FROM movement m
        GROUP BY m.id
    ),
    w2 AS (
        SELECT MAX(c.transact_id) AS transact_id, c.id
        FROM callin c
        GROUP BY c.id
    )
    SELECT COUNT(m.id) AS num_moves, SUM(tracked.tracked) AS num_tracked, 
    CAST(CAST(SUM(tracked.tracked) AS DECIMAL(7,2)) / CAST(COUNT(m.id) AS DECIMAL(7,2)) AS DECIMAL(7,2)) AS tracked_perc 
    FROM (SELECT m.* FROM movement m JOIN w1 ON m.id = w1.id AND m.transact_id = w1.transact_id) m
    LEFT JOIN (
        SELECT CASE WHEN COUNT(id) > 0 THEN 1 ELSE 0 END AS tracked, movement_id
        FROM (SELECT c.* FROM callin c JOIN w2 ON c.id = w2.id AND c.transact_id = w2.transact_id) c
        WHERE (latitude IS NOT NULL OR longitude IS NOT NULL)
        GROUP BY movement_id
    ) tracked ON tracked.movement_id = m.id
    WHERE m.id IN ({movement_ids_str})
    """
    return execute_athena_query(query)[0]  # Assuming the first row contains the summary data

def query_ontime_info(movement_ids):
    movement_ids_str = ','.join(f"'{m}'" for m in movement_ids)
    query = f"""
    WITH w1 AS (
        SELECT MAX(s.transact_id) AS transact_id, s.id
        FROM stop s
        GROUP BY s.id
    )
    SELECT COUNT(on_time.id) AS num_stops, SUM(on_time.on_time) AS num_on_time_stops, 
    CAST(CAST(SUM(on_time.on_time) AS DECIMAL(7,2)) / CAST(COUNT(on_time.id) AS DECIMAL(7,2)) AS DECIMAL(7,2)) AS on_time_perc
    FROM (
        SELECT movement_id, id, actual_arrival, 
        CASE WHEN sched_arrive_late IS NULL THEN sched_arrive_early ELSE sched_arrive_late END AS sched_arrive,
        CASE WHEN actual_arrival <= DATE_ADD('minute', 60, (CASE WHEN sched_arrive_late IS NULL THEN sched_arrive_early ELSE sched_arrive_late END)) THEN 1 ELSE 0 END AS on_time
        FROM (SELECT s.* FROM stop s JOIN w1 ON s.id = w1.id AND s.transact_id = w1.transact_id)
        WHERE movement_id IN ({movement_ids_str})
    ) on_time
    """
    return execute_athena_query(query)[0]  # Assuming the first row contains the summary data



def execute_athena_query(query):
    # Replace these values with your own
    role_arn = 'arn:aws:iam::332281781429:role/rep-assignment-to-athena'
    session_name = 'AthenaQuerySession'

    # Assume the role
    sts_client = boto3.client('sts')
    assumed_role = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name
    )

    credentials = assumed_role['Credentials']

    # Create a session with the assumed role credentials
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    # Create an Athena client using the session
    athena_client = session.client('athena', region_name='us-east-1')

    # Start the query execution
    query_start = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': 'dw-etl-lvlp-prod'}  # Replace with your database name  # Replace with your bucket name
    )

    query_execution_id = query_start['QueryExecutionId']
    query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)

    while query_status['QueryExecution']['Status']['State'] in ['RUNNING', 'QUEUED']:
        query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        time.sleep(2)

    if query_status['QueryExecution']['Status']['State'] != 'SUCCEEDED':
        raise Exception(f"Query failed: {query_status['QueryExecution']['Status']['StateChangeReason']}")

    result_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
    result_data = []
    headers = [col['Name'] for col in result_response['ResultSet']['ResultSetMetadata']['ColumnInfo']]
    for row in result_response['ResultSet']['Rows'][1:]:  # Skip header row
        result_data.append({headers[i]: col.get('VarCharValue', None) for i, col in enumerate(row['Data'])})

    return result_data
