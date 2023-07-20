import boto3
import re

table_name = "stosc_xero_member_payments"

dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id="xxx", aws_secret_access_key="xxx",
        region_name="ap-southeast-1",
    )
table = dynamodb.Table(table_name)
response = table.scan()
items = response['Items']
while True:
    # loop through the items and delete the records that match the condition
    for item in items:
        # Items that do not start with a digit
        if not re.match("^\d", item['AccountCode'] ):
            table.delete_item(Key={'ContactID': item['ContactID'],'AccountCode': item['AccountCode'] })
            print(f"Deleted {item}")
    # if there are more items to scan, continue scanning
    if 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items = response['Items']
    # if all items have been scanned, exit the loop
    else:
        break

