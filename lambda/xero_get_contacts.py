# xero_get_contacts.py
import json, os
import xero_utils
import pandas as pd

file_name = "/tmp/xero_contacts.csv"

def get_Xero_Contacts():
    has_more_pages = True
    page = 0
    contacts = []
    _contacts = {}
    # Go through pages (100 per page)
    while has_more_pages:
        page += 1
        url = f'https://api.xero.com/api.xro/2.0/Contacts?summaryOnly=True&page={page}'
        xero_contacts = xero_utils.xero_get(url)
        if len(xero_contacts["Contacts"]) == 0:
            has_more_pages = False
        else:
            _contacts = [
                {
                    "memberCode": _contact['AccountNumber'],
                    "Name": _contact['FirstName'] + ' ' + _contact['LastName'] if 'LastName' in _contact else '',
                    "ContactID": _contact['ContactID']
                }
                for _contact in xero_contacts['Contacts']
                if (
                    'AccountNumber' in _contact
                    # Exclude other contacts who have account numbers
                    and len(_contact['AccountNumber']) == 4
                    and _contact['ContactStatus'] == 'ACTIVE'
                )
            ]
            contacts.extend(_contacts)
    return contacts
    
def lambda_handler(event, context):
    print(f" Getting Member List...")
    list_Contacts = get_Xero_Contacts()
    print(f"Retrieved {len(list_Contacts)} members.")
    df_contacts = pd.DataFrame(list_Contacts)
    print(f"{df_contacts.head(2)}\n")
    df_contacts.sort_values(by=['memberCode']).to_csv(file_name, index=False)
    
    #return f"Generated {file_name}"
    return {
            'headers': { "Content-type": "text/csv" },
            'statusCode': 200,
            'body': df_contacts.sort_values(by=['memberCode']).to_csv(),
        }