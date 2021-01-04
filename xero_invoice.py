import json
import logging
import string
import my_secrets

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

contacts = open("contacts.txt", "r")

# For each member ID
for _contact in contacts:
    _contactID = get_ContactID(_contact[:4])
    if _contactID:

        # Get all Invoices for this contact 
        url = f"https://api.xero.com/api.xro/2.0/Invoices?ContactIDs={_contactID}&Statuses=AUTHORISED"
        # Get Invoices Created only this year 
        _header = {'If-Modified-Since': utils.year_start()}
        invoices = xero_get(url,**_header)

        for invoice in invoices['Invoices']:
            print(color(f"===============\nCustomer ID: {_contact}",Colors.purple))

            # Only for FY 21 invoices
            if invoice['InvoiceNumber'].startswith('INV-21'):
                if invoice['Status'] == 'AUTHORISED':
                    # 01. Rename the invoice
                    new_invoice_data = {}
                    contact = {}
                    lineItems = {}
                    
                    lineItems['LineItemID'] = invoice['LineItems'][0]['LineItemID']
                    lineItems['Description'] = "Subscription 2021"
                    lineItems['Quantity'] = 1.0
                    lineItems['UnitAmount'] = invoice['LineItems'][0]['UnitAmount']
                    lineItems['TotalTax'] = 0.0
                    lineItems['AccountCode'] = '3010'
                    lineItem_Array = [lineItems]

                    contact['ContactID'] = _contactID

                    new_invoice_data['Type'] = 'ACCREC'
                    new_invoice_data['Contact'] = contact
                    new_invoice_data['Date'] = '2021-01-01'
                    new_invoice_data['DueDate'] = '2021-12-31'
                    new_invoice_data['LineAmountTypes'] = 'NoTax'
                    
                    # Rename Invoice
                    new_invoice_data['InvoiceNumber'] = invoice['InvoiceNumber'] + "-VOID"
                    new_invoice_data['LineItems'] = lineItem_Array

                    print(color(f"Updating {invoice['InvoiceNumber']} to {new_invoice_data['InvoiceNumber']}",Colors.orange))
                    url = f"https://api.xero.com/api.xro/2.0/Invoices/{invoice['InvoiceID']}"
                    rename_invoice_response =  xero_post(url,new_invoice_data)
                    if rename_invoice_response.status_code == 200:
                        print(color("SUCCESS\n",Colors.green))
                    else:
                        print(rename_invoice_response.text)

                    # 02. Void Invoice
                    if rename_invoice_response.status_code == 200:
                        void_invoice_data = {}
                        void_invoice_data['InvoiceNumber'] = new_invoice_data['InvoiceNumber']
                        # Set Status to VOID
                        void_invoice_data['Status'] = 'VOIDED'
                        print(color(f"Voiding {void_invoice_data['InvoiceNumber']}",Colors.red))
                        url = f"https://api.xero.com/api.xro/2.0/Invoices/{void_invoice_data['InvoiceNumber']}"
                        void_invoice_response =  xero_post(url,void_invoice_data)
                        if void_invoice_response.status_code == 200:
                            print(color("SUCCESS\n",Colors.green))
                        else:
                            print(void_invoice_response.text)

                    # 03. Create new replacement Invoice
                    if void_invoice_response.status_code == 200:
                        new_invoice_data['InvoiceNumber'] = invoice['InvoiceNumber']
                        new_invoice_data['LineItems'][0].pop('LineItemID')

                        print(color(f"Creating {new_invoice_data['InvoiceNumber']}",Colors.blue))
                        url = f"https://api.xero.com/api.xro/2.0/Invoices/"
                        create_invoice_response =  xero_post(url,new_invoice_data)
                        if create_invoice_response.status_code == 200:
                            print(color("SUCCESS\n",Colors.green))
                        else:
                            print(create_invoice_response.text)

contacts.close()