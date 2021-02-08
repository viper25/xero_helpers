import json
import logging
import string
import my_secrets
from datetime import date
import datetime
import requests
import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO Hardcoded Tenant ID
xero_tenant_id = my_secrets.xero_tenant_ID
   
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
       print(color(f"Too many requests. Try after {response.headers._store['retry-after'][1]} seconds", Colors.red))  
       raise
    else:
        return response.json()

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
        

def get_ContactID(code = None):
    if code is None:
        url = 'https://api.xero.com/api.xro/2.0/Contacts'        
        contacts = xero_get(url)
    else:
        # https://developer.xero.com/documentation/api/contacts#optimised-queryparameters
        url = f'https://api.xero.com/api.xro/2.0/Contacts?where=AccountNumber=="{code}"'
        contacts = xero_get(url)
        if len(contacts['Contacts'])>0:
            return contacts['Contacts'][0]['ContactID']
        else:
            return None

def parse_Xero_Date(_date):
    return datetime.date.fromtimestamp(int(_date[6:-2].split('+')[0])/1000)

today = date.today()
members_outstanding = {}
with open("contacts.txt", "r") as contacts:
    # For each member ID
    #contacts = ['B008']
    for _contact in contacts:
        # Remove newline char
        _contact = _contact.strip()
        #print(color(f"Processing {_contact[:4]}",Colors.yellow))
        _contactID = get_ContactID(_contact[:4])
        if _contactID:

            # Get all Invoices for this contact 
            url = f"https://api.xero.com/api.xro/2.0/Invoices?ContactIDs={_contactID}&Statuses=AUTHORISED,PAID,DRAFT"
            # Get Invoices Created only this year 
            _header = {'If-Modified-Since': utils.year_start()}
            invoices = xero_get(url,**_header)

            for invoice in invoices['Invoices']:
                print(color(f"{invoice['InvoiceNumber']} ({invoice['Status']}) for {_contact}",Colors.white))

                # Only for FY 21 invoices
                if invoice['InvoiceNumber'].startswith('INV-21'):
                    if (invoice['Status'] == 'AUTHORISED') or (invoice['Status'] == 'DRAFT'):
                        percentage_Paid = invoice['AmountPaid']/invoice['Total']
                        percentage_days_of_year = (today - date(date.today().year, 1, 1)).days/365
                        delta = abs(percentage_Paid - percentage_days_of_year)

                        # A user hasn't paid > 50% of his dues taking into account time passed in the year
                        if delta > my_secrets.payment_delta:
                            members_outstanding[_contact] = abs(percentage_Paid - percentage_days_of_year)
                            print(color(f"{_contact[:4]} is outstanding by {round(delta*100,1)} % ",Colors.red))
                            #print(f"{percentage_Paid} - {percentage_days_of_year} = {abs(percentage_Paid - percentage_days_of_year)}")
                        else:
                            print(color(f"{_contact[:4]} payment delta = {round(delta*100,1)} % ",Colors.blue))
                            members_outstanding[_contact] = round(delta,1)
                    elif invoice['Status'] == 'PAID':
                        members_outstanding[_contact] = 0
                        print(color(f"{_contact[:4]} has cleared all dues ",Colors.green))

        print("---------------------------")

print("DONE")