""" 
Generate Xero Contacts File that contains mapping of Xero contactID to memberID for 
future easy lookup
"""
import utils

# https://github.com/CodeForeverAndEver/ColorIt
from colorama import init, Fore, Back, Style, deinit
import pandas as pd
import logging

init(autoreset=True)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

file_name = "csv\\xero_contacts.csv"
# Use this to ensure that ColorIt will be usable by certain command line interfaces


def get_Xero_Contacts():
    has_more_pages = True
    page = 0
    contacts = []
    _contacts = {}
    # Go through pages (100 per page)
    while has_more_pages:
        page += 1
        print(f"{Fore.YELLOW}  Processing Page {page} of contacts...")
        url = f'https://api.xero.com/api.xro/2.0/Contacts?summaryOnly=True&page={page}'
        xero_contacts = utils.xero_get(url)
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

def Xero_Contact_List():
    print(f"{Fore.WHITE}Getting Member List...")
    list_Contacts = get_Xero_Contacts()
    print(f"{Fore.YELLOW}Retrieved {Fore.GREEN}{len(list_Contacts)}{Fore.YELLOW} members. Sample Listing:")
    df_contacts = pd.DataFrame(list_Contacts)
    print(f"{Fore.BLUE}{df_contacts.head(2)}\n")
    df_contacts.sort_values(by=['memberCode']).to_csv(file_name, index=False)
    print(f"{Fore.WHITE}Written to {file_name}")


if __name__ == '__main__':
    Xero_Contact_List()