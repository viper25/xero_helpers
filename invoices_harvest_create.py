"""
▶ Create New invoices - for Harvest festival or Annual Subscription
▶ Input file for harvest Festival is a CSV *HAS* to have list ORDERED by Member Code. Format:
    61-Mango & Pineapple,W002-Josey,200
    62-Pineapple,W002-Josey,120
▶ Set the NEXT invoice in Xero (https://go.xero.com/InvoiceSettings/InvoiceSettings.aspx) to HF-22-0001
    Do remember to revert back to INV-22-XXX after the harvest festival invoices are generated
▶ Account Code 3200 to exist 
▶ Check Tenant IDs in mysecrets.py. If using Demo Tenant, get it's TenantID using xero_first_time.py
▶ ❗ Set Variables Below 
"""

import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import my_secrets

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# Ensure the CSV is sorted by member name
csv_file = "csv\harvest_invoices.csv"
list_of_well_wishers = ['W001','W002','W003','W004','W005','W006','W007']
STOSC_WELL_WISHER_CONTACT_ID = 'xxx'

def create_xero_invoice(inv):
    response =  utils.xero_post("https://api.xero.com/api.xro/2.0/Invoices/",inv)
    if response['Status'] == "OK":
        return response
    else:
        print(color(f"{response['Elements'][0]['ValidationErrors'][0]['Message']}",Colors.red))
        return None

# Initialize variables
new_invoice_data = {}
_current_member_code = ''

# Just a failsafe check
if my_secrets.xero_tenant_ID == 'xxx':
    print(color(f"CAREFUL!: This is STOSC PRODUCTION ACCOUNT. Are you sure?",Colors.red))
    print(color(f"Did you set NEXT Invoice Numbers? to HF-21-001? ",Colors.red))
    print(color(f"Is your CSV ordered by member code? ",Colors.red))
    sys.exit(0)

with open(csv_file, 'r') as f:
    for line in f:        
        line = line.strip()
        if line:
            item, member, price = line.split(',')
            # 7-Wincarnis Ginger Wine --> As extracted from DDB. 
            item = item.split('-')[1]
            # A038-Ajish P I
            member_code_from_file = member.split('-')[0]
            if _current_member_code != member_code_from_file:
                # We have a new member code so let's send the Invoice created so far.
                if new_invoice_data:
                    invoice = create_xero_invoice(new_invoice_data)
                    if invoice:
                        print(color(f"Created Invoice {invoice['Invoices'][0]['InvoiceNumber']} ({invoice['Invoices'][0]['Status']}) for {_current_member_code}\n",Colors.green))
                    else:
                        print(color(f"Invoice not created",Colors.red))                    
                # Reset the Invoice to start creating a new Invoice
                new_invoice_data = {}
                new_invoice_data['LineItems'] = []
                # Fetch ContactID since the member code has changed
                if member_code_from_file in list_of_well_wishers:
                    # Well Wisher's Contact ID
                    _contactID = STOSC_WELL_WISHER_CONTACT_ID
                else:
                    _contactID = utils.get_ContactID(member_code_from_file)
            if _contactID:        
                print(color(f"Processing {item} for {member} for ${price}",Colors.white))
                _current_member_code = member_code_from_file
                contact = {}
                lineItem = {}
                # Should we list each item individually? 
                lineItem['Description'] = item
                lineItem['Quantity'] = 1.0
                lineItem['UnitAmount'] = price
                lineItem['TaxType'] ="NONE"
                lineItem['AccountCode'] = '3200'


                new_invoice_data['Type'] = 'ACCREC'
                contact['ContactID'] = _contactID
                new_invoice_data['Contact'] = contact
                new_invoice_data['Date'] = '2022-11-07'
                new_invoice_data['DueDate'] = '2022-12-01'
                new_invoice_data['LineAmountTypes'] = 'NoTax'
                new_invoice_data['Reference'] = 'Harvest Festival 2022'
                new_invoice_data['Status'] = 'AUTHORISED'

                # Add the Line Item to the Invoice
                new_invoice_data['LineItems'].append(lineItem)
            else:
                print(color(f"ERROR: No ContactID for {member_code_from_file}",Colors.red))
    
    # Create the last Invoice at the end of the loop
    invoice = create_xero_invoice(new_invoice_data)
    if invoice:
        print(color(f"Created Invoice {invoice['Invoices'][0]['InvoiceNumber']} ({invoice['Invoices'][0]['Status']}) for {_current_member_code}\n",Colors.green))
    else:
        print(color(f"Invoice not created",Colors.red))                  


print(color(f"Remember to reset the Invoice Numbering",Colors.blue))                  