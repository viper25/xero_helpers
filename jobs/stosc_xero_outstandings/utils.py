import datetime
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import requests
import time
import tomli

with open("config.toml", "rb") as f:
    toml_dict = tomli.load(f)

# TODO Hardcoded Tenant ID
xero_tenant_id = toml_dict['xero']['XERO_TENANT_ID']
REFRESH_TOKEN_KEY = "xero-helpers"
resource = boto3.resource('dynamodb', aws_access_key_id=toml_dict['ddb_srvc_stosc_members']['STOSC_DDB_ACCESS_KEY_ID'], aws_secret_access_key=toml_dict['ddb_srvc_stosc_members']['STOSC_DDB_SECRET_ACCESS_KEY'], region_name='ap-southeast-1')
table = resource.Table('stosc_xero_tokens')
#-----------------------------------------------------------------------------------    
# ------------------------------------------------------
# Refresh access_token. Use the refresh_token to keep the access_token "fresh" every 30 mins. 
def __xero_get_Access_Token():
    # Get current refresh token. Use xoauth.exe to generate a new one if it's expired    
    response=table.query(KeyConditionExpression=Key('token').eq(REFRESH_TOKEN_KEY))
    old_refresh_token = response['Items'][0]['refresh_token']
    
    url = 'https://identity.xero.com/connect/token'
    response = requests.post(url,headers={
        'Content-Type' : 'application/x-www-form-urlencoded'},data={
            'grant_type': 'refresh_token',            
            'client_id' : toml_dict['xero']['XERO_CLIENT_ID'],
            'refresh_token': old_refresh_token
            })
    response_dict = response.json()
    current_refresh_token = response_dict['refresh_token']

    # Set new refresh token
    chunk = {"token":REFRESH_TOKEN_KEY, 'refresh_token':current_refresh_token, 'modified_ts': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    table.put_item(Item=chunk)

    return response_dict['access_token']

#-----------------------------------------------------------------------------------    
# Make the GET HTTP call to XERO API
def xero_get(url, **extra_headers):
    _headers = {
        'Authorization': 'Bearer ' + __xero_get_Access_Token(),
        'Accept': 'application/json',
        'Xero-tenant-id': xero_tenant_id
    }
    # Some API calls require adding the modified date to get just this year's transaction and 
    # not from the very begining
    if extra_headers: 
        _headers.update(extra_headers)
    response = requests.get(url,headers=_headers)
    if response.status_code == 429:
       print(f"Too many requests. Trying after {int(response.headers._store['retry-after'][1]) + 5} seconds")
       time.sleep(int(response.headers._store['retry-after'][1]) + 5)
       # Try ONCE more (assuming this time it DOESN'T error)
       response = requests.get(url,headers=_headers)
       return response.json()
    else:
        return response.json()
