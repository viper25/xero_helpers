"""
▶ Create New invoices - for Annual Subscription based on prevoius years invoice amount
▶ Input file is a text file of Member Codes. It's good (not mandatory that the list be sorted) Format:
    R023
    Z001
  You can also use `generate_Xero_Contact_List.py` to generate the csv file of the format:
    R023,Reji K Varghese,208dd022-9620-4aef-b515-f00b726bd1a8
  The code will handle both types of files.
▶ Set the NEXT invoice in Xero (https://go.xero.com/InvoiceSettings/InvoiceSettings.aspx) to HF-22-0001
▶ Account Code 3010 to exist (Member Subscription)
▶ Check Tenant IDs in mysecrets.py. If using Demo Tenant, get it's TenantID using xero_first_time.py
▶ ❗ We assume the subscription amount is the same as last year. Override manually if not so!    
▶ ❗ Set Variables Below 
"""

import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import my_secrets

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# Ensure the CSV is sorted by member name
# csv_file = "csv\xero_contacts.csv"
csv_file = "csv\contacts.txt"

INVOICE_DESC = 'Subscription 2022'
SUBSCRIPTION_ACCOUNT_CODE = '3010'
INVOICE_DATE  = '2022-01-01'
INVOICE_DUE_DATE = '2022-12-31'
# Look for Invoices starting with this prefix to determine a members previous subscription
SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION = 'INV-21'

def create_xero_invoice(inv):
    response =  utils.xero_post("https://api.xero.com/api.xro/2.0/Invoices/",inv)
    if response.status_code == 200:
        return response.json()        
    else:
        print(color(f"{response.json()['Elements'][0]['ValidationErrors'][0]['Message']}",Colors.red))
        return None

def get_last_subscription_amount_by_contact_id(contact_id):
    list_last_invoice = []
    list_of_invoices = []
    list_of_invoices = utils.xero_get(f"https://api.xero.com/api.xro/2.0/Invoices?ContactIDs={contact_id}&Statuses=AUTHORISED")
    if len(list_of_invoices['Invoices']) > 0:
        # Get latest subscription amount
        list_last_invoice = [x for x in list_of_invoices['Invoices'] if x["InvoiceNumber"].startswith(SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION)]
        if len(list_last_invoice) == 1:
            return list_last_invoice[0]['Total']
        elif len(list_last_invoice) == 0:
            print(color(f"{member_code} has no previous subscription for '{SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION}-*'; Skipping",Colors.red))
            return None 
        elif len(list_last_invoice) > 1:
            print(color(f"{member_code} has more than one subscription for '{SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION}-*'; setting to 0",Colors.red))
            return 0
    else:
        print(color(f"No Invoices found for {member_code}",Colors.red))
        return None


# Initialize variables
new_invoice_data = {}

# Just a failsafe check
if my_secrets.xero_tenant_ID == 'f7dc56b9-fe29-43cf-be0a-a5488da4e30f':
    print(color(f"CAREFUL!: This is STOSC PRODUCTION ACCOUNT. Are you sure?",Colors.red))
    print(color(f"Did you set NEXT Invoice Numbers? to INV-22-001? ",Colors.red))
    sys.exit(0)

with open(csv_file, 'r') as f:
    for member_code in f:
        member_code = member_code.strip()
        if member_code:
            new_invoice_data = {}
            new_invoice_data['LineItems'] = []
            print(color(f"\nProcessing {member_code}",Colors.white))
            _contactID = utils.get_ContactID(member_code)
            if _contactID:
                contact = {}
                lineItems = {}
                lineItems['Description'] = INVOICE_DESC
                lineItems['Quantity'] = 1.0
                last_subscription_amount = get_last_subscription_amount_by_contact_id(_contactID)
                if last_subscription_amount:
                    lineItems['UnitAmount'] = last_subscription_amount
                else:
                    continue
                lineItems['TaxType'] ="NONE"
                lineItems['AccountCode'] = SUBSCRIPTION_ACCOUNT_CODE


                new_invoice_data['Type'] = 'ACCREC'
                contact['ContactID'] = _contactID
                new_invoice_data['Contact'] = contact
                new_invoice_data['Date'] = INVOICE_DATE
                new_invoice_data['DueDate'] = INVOICE_DUE_DATE
                new_invoice_data['LineAmountTypes'] = 'NoTax'
                new_invoice_data['Reference'] = 'Subscription 2022'
                new_invoice_data['Status'] = 'AUTHORISED'

                # Add the Line Item to the Invoice
                new_invoice_data['LineItems'].append(lineItems)
                # Create the Invoice
                invoice = create_xero_invoice(new_invoice_data)
                if invoice:
                    print(color(f"Created Invoice {invoice['Invoices'][0]['InvoiceNumber']} ({invoice['Invoices'][0]['Status']}) for {member_code}",Colors.green))
                else:
                    print(color(f"Invoice not created",Colors.red))
            else:
                print(color(f"ERROR: No Xero ContactID for {member_code}",Colors.red))
    
print(color(f"Done! 👍🏻",Colors.blue))                  