import boto3

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

# Get a reference to an existing table
def get_table(table_name):
    table = dynamodb.Table(table_name)
    return table

# Put an item into a table
def put_item(table, item):
    response = table.put_item(Item=item)
    print("PutItem succeeded:", response)

# Get an item from a table using its primary key
def get_item(table, key):
    response = table.get_item(Key=key)
    item = response.get('Item')
    return item

# Update an item in a table
def update_item(table, key, update_expression, expression_attribute_values):
    response = table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )
    print("UpdateItem succeeded:", response)

# Delete an item from a table using its primary key
def delete_item(table, key):
    response = table.delete_item(Key=key)
    print("DeleteItem succeeded:", response)

# Query items in a table
def query_items(table, key_condition_expression, expression_attribute_values):
    response = table.query(
        KeyConditionExpression=key_condition_expression,
        ExpressionAttributeValues=expression_attribute_values
    )
    items = response.get('Items', [])
    return items

# Scan all items in a table
def scan_table(table):
    response = table.scan()
    items = response.get('Items', [])
    return items
