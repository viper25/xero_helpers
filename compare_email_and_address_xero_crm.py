'''
Compare addresses between Xero and CRM systems
'''
import tomllib
import db
import utils
from colorama import init, Fore

init(autoreset=True)

# Load config
with open("config.toml", "rb") as f:
    config = tomllib.load(f)

FILE_MEMBERS = config['gb_eligibility']['FILE_MEMBERS']

def get_zip_from_xero(contactID:str)->str:
    url = f'https://api.xero.com/api.xro/2.0/Contacts/{contactID}'
    xero_contacts = utils.xero_get(url)
    if 'PostalCode' in xero_contacts['Contacts'][0]['Addresses'][0] and xero_contacts['Contacts'][0]['Addresses'][0]['PostalCode'] != "":
        return xero_contacts['Contacts'][0]['Addresses'][0]['PostalCode']
    elif 'PostalCode' in xero_contacts['Contacts'][0]['Addresses'][1]:
        return xero_contacts['Contacts'][0]['Addresses'][1]['PostalCode']

def get_email_from_xero(contactID:str)->str:
    url = f'https://api.xero.com/api.xro/2.0/Contacts/{contactID}'
    xero_contacts = utils.xero_get(url)
    if 'EmailAddress' in xero_contacts['Contacts'][0] and xero_contacts['Contacts'][0]['EmailAddress'] != "":
        return xero_contacts['Contacts'][0]['EmailAddress']

# Loop through active users in CRM
with open(FILE_MEMBERS, "r") as f:
    for line in f:
        eligibility = False
        line = line.strip()
        if line.startswith("memberCode"):
            continue
        if line:
            memberCode, Name, contactID = line.split(",")
            if memberCode == 'C000':
                continue
            # print(f"{Fore.WHITE}Comparing addresses for {Name} ({memberCode})")
            email_from_crm = db.get_email(memberCode)
            email_from_xero = get_email_from_xero(contactID)
            if (email_from_crm and email_from_xero) and (email_from_crm.strip() != email_from_xero.strip()):
                print(f"{Fore.RED}{Name} ({memberCode}) has {email_from_crm} in CRM and {email_from_xero} in Xero")

            # zip_from_crm = db.get_address(memberCode)
            # zip_from_xero = get_zip_from_xero(contactID)
            # if zip_from_crm.strip() != zip_from_xero.strip():
            #     print(f"{Fore.RED}{Name} ({memberCode}) has {zip_from_crm} in CRM and {zip_from_xero} in Xero")
print("Done")