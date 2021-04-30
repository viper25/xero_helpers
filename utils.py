from datetime import date
import datetime
import os
import requests
import my_secrets

# TODO Hardcoded Tenant ID
xero_tenant_id = my_secrets.xero_tenant_ID

#-----------------------------------------------------------------------------------    
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d")

# ------------------------------------------------------
# Refresh access_token. Use the refresh_token to keep the access_token "fresh" every 30 mins. 
def xero_get_Access_Token():
    cwd = os.getcwd()
    f = open(f"{os.path.join(cwd,'xero_refresh_token.txt')}", 'r')
    old_refresh_token = f.read()
    f.close()
    
    url = 'https://identity.xero.com/connect/token'
    response = requests.post(url,headers={
        'Content-Type' : 'application/x-www-form-urlencoded'},data={
            'grant_type': 'refresh_token',
            'client_id' : my_secrets.xero_client_id,
            'refresh_token': old_refresh_token
            })
    response_dict = response.json()
    current_refresh_token = response_dict['refresh_token']

    xero_output = open(f"{os.path.join(cwd,'xero_refresh_token.txt')}", 'w')
    xero_output.write(current_refresh_token)
    xero_output.close()
    return response_dict['access_token']

#-----------------------------------------------------------------------------------    
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
    response = requests.get(url,headers=_headers)
    if response.status_code == 429:
       print(color(f"Too many requests. Trying after {int(response.headers._store['retry-after'][1]) + 5} seconds", Colors.red))  
       time.sleep(int(response.headers._store['retry-after'][1]) + 5)
       # Try ONCE more (assuming this time it DOESN'T error)
       response = requests.get(url,headers=_headers)
       return response.json()
    else:
        return response.json()

#-----------------------------------------------------------------------------------    

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
        response = requests.post(args[0],headers=_headers,json=args[1])
        return response
    except Exception as e:
        return "Error" + e

#-----------------------------------------------------------------------------------    
# Parse weird Xero dates of format: /Date(1618963200000+0000)/
def parse_Xero_Date(_date):
    return datetime.datetime.fromtimestamp(int(_date[6:-2].split('+')[0])/1000)