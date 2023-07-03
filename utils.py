from datetime import date
import datetime
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import requests
import logging
from colorit import *
import time
import tomllib

with open("config.toml", "rb") as f:
    toml_dict = tomllib.load(f)

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# TODO Hardcoded Tenant ID
xero_tenant_id = toml_dict['xero']['XERO_TENANT_ID']
REFRESH_TOKEN_KEY = "xero-helpers"
resource = boto3.resource('dynamodb', aws_access_key_id=toml_dict['ddb_srvc_stosc_members']['STOSC_DDB_ACCESS_KEY_ID'],
                          aws_secret_access_key=toml_dict['ddb_srvc_stosc_members']['STOSC_DDB_SECRET_ACCESS_KEY'],
                          region_name='ap-southeast-1')
table = resource.Table('stosc_xero_tokens')


# -----------------------------------------------------------------------------------
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d")


# ------------------------------------------------------
# Refresh access_token. Use the refresh_token to keep the access_token "fresh" every 30 mins. 
def __xero_get_Access_Token():
    # Get current refresh token. Use xoauth.exe to generate a new one if it's expired    
    response = table.query(KeyConditionExpression=Key('token').eq(REFRESH_TOKEN_KEY))
    old_refresh_token = response['Items'][0]['refresh_token']

    url = 'https://identity.xero.com/connect/token'
    response = requests.post(url, headers={
        'Content-Type': 'application/x-www-form-urlencoded'}, data={
        'grant_type': 'refresh_token',
        'client_id': toml_dict['xero']['XERO_CLIENT_ID'],
        'refresh_token': old_refresh_token
    })
    response_dict = response.json()
    current_refresh_token = response_dict['refresh_token']

    # Set new refresh token
    chunk = {"token": REFRESH_TOKEN_KEY, 'refresh_token': current_refresh_token,
             'modfied_ts': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    table.put_item(Item=chunk)

    return response_dict['access_token']


# -----------------------------------------------------------------------------------
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
        'Authorization': 'Bearer ' + __xero_get_Access_Token(),
        'Accept': 'application/json',
        'Xero-tenant-id': xero_tenant_id
    }

    if extra_headers:
        _headers.update(extra_headers)
    try:
        response = requests.post(args[0], headers=_headers, json=args[1])
        if response.status_code == 429:
            print(color(f"Too many requests. Trying after {int(response.headers._store['retry-after'][1]) + 5} seconds",
                        Colors.red))
            time.sleep(int(response.headers._store['retry-after'][1]) + 5)
            # Try ONCE more (assuming this time it DOESN'T error)
            requests.post(args[0], headers=_headers, json=args[1])
            return response.json()
        else:
            return response.json()
    except Exception as e:
        return "Error" + e


# -----------------------------------------------------------------------------------
# Parse weird Xero dates of format: /Date(1618963200000+0000)/
def parse_Xero_Date(_date):
    return datetime.fromtimestamp(int(_date[6:-2].split('+')[0]) / 1000)


# -----------------------------------------------------------------------------------
# Get the Xero Contact ID from the Account Code
def get_ContactID(code=None):
    if code is None:
        url = 'https://api.xero.com/api.xro/2.0/Contacts'
        contacts = xero_get(url)
    else:
        # https://developer.xero.com/documentation/api/contacts#optimised-queryparameters
        # https://api-explorer.xero.com/accounting/contacts/getcontacts?query-where=AccountNumber%3D%3D%22B030%22
        url = f'https://api.xero.com/api.xro/2.0/Contacts?where=AccountNumber=="{code}"'
        contacts = xero_get(url)
        if ('Contacts' in contacts) and len(contacts['Contacts']) > 0:
            return contacts['Contacts'][0]['ContactID']
        else:
            return None


# -----------------------------------------------------------------------------------
def get_Invoices(_contactID):
    if _contactID:
        url = f'https://api.xero.com/api.xro/2.0/Invoices?ContactIDs={_contactID}&Statuses=AUTHORISED,PAID&where=Type="ACCREC"'
        # Add If-Modified-Since HTTP header to get this year's invoices only
        # _header={'If-Modified-Since': utils.year_start()}
        # return __xero_get(url,**_header)
        return xero_get(url)


# -----------------------------------------------------------------------------------

def get_last_subscription_amount_by_contact_id(contact_id, member_code):
    list_last_invoice = []
    list_of_invoices = []
    subscription_amt = None
    list_of_invoices = xero_get(
        f"https://api.xero.com/api.xro/2.0/Invoices?ContactIDs={contact_id}&Statuses=AUTHORISED,PAID"
    )
    if len(list_of_invoices["Invoices"]) > 0:
        # Get latest subscription amount
        list_last_invoice = [
            x for x in list_of_invoices["Invoices"] if
            x["InvoiceNumber"].startswith(SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION)
        ]
        if len(list_last_invoice) == 1:
            subscription_amt = list_last_invoice[0]["Total"]
            if "pro" in list_last_invoice[0]['LineItems'][0]['Description']:
                my_logger.info(f"\t{member_code} has pro-rated subscription - fix manually", Colors.orange)
        elif len(list_last_invoice) == 0:
            my_logger.warn(
                f"{member_code} has no previous subscription for '{SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION}-*'; Skipping"
            )
            subscription_amt = None
        elif len(list_last_invoice) > 1:
            my_logger.warn(
                f"{member_code} has more than one subscription for '{SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION}-*'; setting to 0"
            )
            subscription_amt = 0
    else:
        my_logger.warn(f"No Invoices found for {member_code}")
        return None
    return subscription_amt


# -----------------------------------------------------------------------------------
#         
def string_to_bytes(string):
    return bytes(string, 'utf-8')


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="xero.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)


# Override the logging functionality to use colorit
class my_logger():
    def warn(msg):
        print(color(f"{msg}", Colors.red))
        logging.warning(msg)

    def error(msg):
        print(color(f"{msg}", Colors.red))
        logging.error(msg)

    def info(msg, Color=Colors.white):
        print(color(f"{msg}", Color))
        logging.info(msg)
