"""
Crete New invoices - for Harvest festival or Annual Subscription
Input file for harvest Festival is a CSV *HAS* to have list ordered by Member Code
Set the NEXT invoice in Xero (https://go.xero.com/InvoiceSettings/InvoiceSettings.aspx) to HF-21-0001
"""

import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import my_secrets

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# Ensure the CSV is sorted by member name
csv_file = "csv\harvest_invoices.csv"
list_of_well_wishers = ['W001','W002','W003','W004','W005']
STOSC_WELL_WISHER_CONTACT_ID = 'xxx'

def create_xero_invoice(inv):
    response =  utils.xero_post("https://api.xero.com/api.xro/2.0/Invoices/",inv)
    if response.status_code == 200:
        return response.json()        
    else:
        print(color(f"{response.json()['Elements'][0]['ValidationErrors'][0]['Message']}",Colors.red))
        return None

# Initialize variables
new_invoice_data = {}
_current_member_code = ''

# Just a failsafe check
if my_secrets.xero_tenant_ID == 'xxx':
    print(color(f"CAREFUL!: This is STOSC PRODUCTION ACCOUNT. Are you sure?",Colors.red))
    print(color(f"Did you set NEXT Invoice Numbers? to HF-21-001? ",Colors.red))
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
                print(color(f"Processing {item} by {member} for ${price}",Colors.white))
                _current_member_code = member_code_from_file
                contact = {}
                lineItems = {}
                # Should we list each item individually? 
                lineItems['Description'] = item
                lineItems['Quantity'] = 1.0
                lineItems['UnitAmount'] = price
                lineItems['TaxType'] ="NONE"
                lineItems['AccountCode'] = '3200'


                new_invoice_data['Type'] = 'ACCREC'
                contact['ContactID'] = _contactID
                new_invoice_data['Contact'] = contact
                new_invoice_data['Date'] = '2021-11-07'
                new_invoice_data['DueDate'] = '2021-12-31'
                new_invoice_data['LineAmountTypes'] = 'NoTax'
                new_invoice_data['Reference'] = 'Harvest Festival 2021'
                new_invoice_data['Status'] = 'AUTHORISED'

                # Add the Line Item to the Invoice
                new_invoice_data['LineItems'].append(lineItems)
            else:
                print(color(f"ERROR: No ContactID for {member_code_from_file}",Colors.red))
    
    # Create the last Invoice at the end of the loop
    invoice = create_xero_invoice(new_invoice_data)
    if invoice:
        print(color(f"Created Invoice {invoice['Invoices'][0]['InvoiceNumber']} ({invoice['Invoices'][0]['Status']}) for {_current_member_code}\n",Colors.green))
    else:
        print(color(f"Invoice not created",Colors.red))                  



    

                    
