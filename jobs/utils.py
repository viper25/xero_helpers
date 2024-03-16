import datetime
from datetime import date
from datetime import datetime

import boto3
import requests
from boto3.dynamodb.conditions import Key

import my_secrets

# TODO Hardcoded Tenant ID
xero_tenant_id = my_secrets.xero_tenant_ID
token_key = "xero-helpers"


# -----------------------------------------------------------------------------------
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d")


# ------------------------------------------------------
# Refresh access_token. Use the refresh_token to keep the access_token "fresh" every 30 mins.
def xero_get_Access_Token():
    # Get current refresh token
    resource = boto3.resource('dynamodb', aws_access_key_id=my_secrets.DDB_ACCESS_KEY_ID,
                              aws_secret_access_key=my_secrets.DDB_SECRET_ACCESS_KEY, region_name='ap-southeast-1')
    table = resource.Table('stosc_xero_tokens')
    response = table.query(KeyConditionExpression=Key('token').eq(token_key))

    old_refresh_token = response['Items'][0]['refresh_token']

    url = 'https://identity.xero.com/connect/token'
    response = requests.post(url, headers={
        'Content-Type': 'application/x-www-form-urlencoded'}, data={
        'grant_type': 'refresh_token',
        'client_id': my_secrets.xero_client_id,
        'refresh_token': old_refresh_token
    })
    response_dict = response.json()
    current_refresh_token = response_dict['refresh_token']

    # Set new refresh token
    chunk = {"token": token_key, 'refresh_token': current_refresh_token,
             'modified_ts': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    table.put_item(Item=chunk)

    return response_dict['access_token']


# -----------------------------------------------------------------------------------
# Make the GET HTTP call to XERO API
def xero_get(url, **extra_headers):
    _headers = {
        'Authorization': 'Bearer ' + xero_get_Access_Token(),
        'Accept': 'application/json',
        'Xero-tenant-id': xero_tenant_id
    }
    # Some API calls require adding the modified date to get just this year's transaction and
    # not from the very begining
    if extra_headers:
        _headers.update(extra_headers)
    response = requests.get(url, headers=_headers)
    if response.status_code == 429:
        print(color(f"Too many requests. Trying after {int(response.headers._store['retry-after'][1]) + 5} seconds",
                    Colors.red))
        time.sleep(int(response.headers._store['retry-after'][1]) + 5)
        # Try ONCE more (assuming this time it DOESN'T error)
        response = requests.get(url, headers=_headers)
        return response.json()
    else:
        return response.json()


# -----------------------------------------------------------------------------------

# Make the POST HTTP call to XERO API
def xero_post(*args, **extra_headers):
    _headers = {
        'Authorization': 'Bearer ' + xero_get_Access_Token(),
        'Accept': 'application/json',
        'Xero-tenant-id': xero_tenant_id
    }

    if extra_headers:
        _headers.update(extra_headers)
    try:
        response = requests.post(args[0], headers=_headers, json=args[1])
        return response
    except Exception as e:
        return "Error" + e


# -----------------------------------------------------------------------------------
# Parse weird Xero dates of format: /Date(1618963200000+0000)/
def parse_Xero_Date(_date):
    return datetime.fromtimestamp(int(_date[6:-2].split('+')[0]) / 1000)


# -----------------------------------------------------------------------------------
def get_chart_of_accounts(status: str = 'ACTIVE', class_type: str = None):
    # https://api.xero.com/api.xro/2.0/Accounts?where=Status="ACTIVE"&&Class="REVENUE"
    # doesn't seem to filter at server side.
    url = f'https://api.xero.com/api.xro/2.0/Accounts'
    accounts = xero_get(url)['Accounts']
    if status:
        accounts = [x for x in accounts if x['Status'] == status]
    if class_type:
        accounts = [x for x in accounts if x['Class'] == class_type]
    return accounts
