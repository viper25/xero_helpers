import json
from datetime import date
import datetime
import time
import utils
import csv
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

def get_ContactID(code = None):
    if code is None:
        url = 'https://api.xero.com/api.xro/2.0/Contacts'        
        contacts = utils.xero_get(url)
    else:
        # https://developer.xero.com/documentation/api/contacts#optimised-queryparameters
        url = f'https://api.xero.com/api.xro/2.0/Contacts?where=AccountNumber=="{code}"'
        contacts = utils.xero_get(url)
        if contacts:
            if len(contacts['Contacts'])>0:
                return contacts['Contacts'][0]['ContactID']
            else:
                return None
        else:
            return None

def export_list(_members_outstanding):
    with open('payments_oustanding.csv', 'w') as f:
        for key in _members_outstanding.keys():
            f.write("%s,%s\n"%(key,_members_outstanding[key]))

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
            invoices = utils.xero_get(url,**_header)

            for invoice in invoices['Invoices']:
                print(color(f"{invoice['InvoiceNumber']} ({invoice['Status']}) for {_contact}",Colors.white))

                # Only for FY 21 invoices
                if invoice['InvoiceNumber'].startswith('INV-21'):
                    if (invoice['Status'] == 'AUTHORISED') or (invoice['Status'] == 'DRAFT'):
                        percentage_Paid = invoice['AmountPaid']/invoice['Total']
                        percentage_days_of_year = (today - date(date.today().year, 1, 1)).days/365
                        ''' 
                        The lower the delta the better:
                        If a member has paid half his dues (50%) by June (50% of the year) then delta = 0
                        In this case he is 100% upto date in payments. If he's paid only 10% of his annual 
                        dues by say Dec (~90%) then his delta is 0.9 - 0.1 = 0.8 (80%) which is > 50% 
                        payment. Therefore he isn't eligible for GB in Dec.
                        If he has paid 90% by say Jun (~50%) then delta = 0.5 - 0.9 = -40% which is < 50% 
                        so he's eligible for GB in Jan
                        '''
                        delta = percentage_days_of_year - percentage_Paid
                        # A user hasn't paid > 50% of his dues taking into account time passed in the year
                        if my_secrets.payment_delta < delta :
                            members_outstanding[_contact] = abs(percentage_Paid - percentage_days_of_year)
                            print(color(f"{_contact[:4]} is outstanding by {round(delta*100,1)} % ",Colors.red))
                            #print(f"{percentage_Paid} - {percentage_days_of_year} = {abs(percentage_Paid - percentage_days_of_year)}")
                        else:
                            print(color(f"{_contact[:4]} payment delta = {round(delta*100,1)} % ",Colors.blue))
                            members_outstanding[_contact] = round(delta,2)
                    elif invoice['Status'] == 'PAID':
                        members_outstanding[_contact] = 0.00
                        print(color(f"{_contact[:4]} has cleared all dues ",Colors.green))

        print("---------------------------")

export_list(members_outstanding)
print("DONE")
