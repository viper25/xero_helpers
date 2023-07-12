"""
CREATE NEW SUBSCRIPTION INVOICES - based on previous years invoice amount
▶ Input file is a text file of Member Codes. It's good (not mandatory that the list be sorted) Format:
    R023
    Z001
  You can also use `generate_Xero_Contact_List.py` to generate the csv file of the format:
    R023,Reji K Varghese,208dd022-9620-4aef-b515-f00b726bd1a8
  The code will handle both types of files.
▶ Set the NEXT invoice in Xero (https://go.xero.com/InvoiceSettings/InvoiceSettings.aspx) to INV-23-0001
▶ Account Code 3010 to exist (Member Subscription)
▶ Check Tenant IDs in mysecrets.py. If using Demo Tenant, get it's TenantID (Demo accounts TenantID changes)
Use xoauth.exe to get an access token, plug that into xero_first_time.py and get the Demo Company TeenantID and update my_secrets.py
▶ ❗ We assume the subscription amount is the same as last year. Override manually if not so!    
▶ ❗ Set Variables Below 
▶ Best to manually debug first (without creating invoices) to see what member codes to remove

Manually check for pro-rated invoices and set to the proper Value.
For FY22: M053, L008, N008, B025, M054 was pro-rated. Check CRM https://crm.stosc.com/churchcrm/v2/family/710
"""

import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *


# Ensure the CSV is sorted by member name
# csv_file = "csv\xero_contacts.csv"
csv_file = "csv\contacts.txt"

INVOICE_YEAR = "2023"
INVOICE_DESC = f"Subscription {INVOICE_YEAR}"
SUBSCRIPTION_ACCOUNT_CODE = "3010"
INVOICE_DATE = f"{INVOICE_YEAR}-01-01"
INVOICE_DUE_DATE = f"{INVOICE_YEAR}-12-31"
# Look for Invoices starting with this prefix to determine a members previous subscription
SEARCH_STRING_FOR_PREVIOUS_SUBSCRIPTION = "INV-22"
# Branding Theme: "STOSC Custom"
# Get this from https://api-explorer.xero.com/accounting/brandingthemes/getbrandingthemes
BRANDING_THEME = "816df8f1-4c58-4696-bb57-a5f56d6288f4"
# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()


# TODO Use Xero Post
def create_xero_invoice(inv):
    response = utils.xero_post("https://api.xero.com/api.xro/2.0/Invoices/", inv)
    if response['Status'] == "OK":
        return response
    else:
        print(color(f"{response.json()['Elements'][0]['ValidationErrors'][0]['Message']}", Colors.red))
        return None

# Initialize variables
new_invoice_data = {}

# Just a failsafe check
# if my_secrets.xero_tenant_ID == "xxx":
#     print(color(f"CAREFUL!: This is STOSC PRODUCTION ACCOUNT. Are you sure?", Colors.red))
#     print(color(f"Did you set NEXT Invoice Numbers? to INV-23-001? ", Colors.red))
#     sys.exit(0)

with open(csv_file, "r") as f:
    for member_code in f:
        member_code = member_code.strip()
        if member_code:
            new_invoice_data = {}
            new_invoice_data["LineItems"] = []
            utils.my_logger.info(f"Processing {member_code}")
            _contactID = utils.get_ContactID(member_code)
            if _contactID:
                contact = {}
                lineItems = {}
                lineItems["Description"] = INVOICE_DESC
                lineItems["Quantity"] = 1.0
                last_subscription_amount = get_last_subscription_amount_by_contact_id(_contactID, member_code)
                if last_subscription_amount:
                    lineItems["UnitAmount"] = last_subscription_amount
                    lineItems["TaxType"] = "NONE"
                    lineItems["AccountCode"] = SUBSCRIPTION_ACCOUNT_CODE
                else:
                    continue

                new_invoice_data["Type"] = "ACCREC"
                contact["ContactID"] = _contactID
                new_invoice_data["Contact"] = contact
                new_invoice_data["Date"] = INVOICE_DATE
                new_invoice_data["DueDate"] = INVOICE_DUE_DATE
                new_invoice_data["LineAmountTypes"] = "NoTax"
                new_invoice_data["Reference"] = INVOICE_DESC
                new_invoice_data["Status"] = "AUTHORISED"
                new_invoice_data["BrandingThemeID"] = BRANDING_THEME

                # Add the Line Item to the Invoice
                new_invoice_data["LineItems"].append(lineItems)
                
                # Create the Invoice
                invoice = None
                invoice = create_xero_invoice(new_invoice_data)
                if invoice:
                    utils.my_logger.info(
                        f"\tCreated Invoice {invoice['Invoices'][0]['InvoiceNumber']} for {member_code}: ${invoice['Invoices'][0]['AmountDue']}",
                        Colors.green,
                    )
                else:
                    utils.my_logger.warn(f"\tInvoice not created for {member_code}")
            else:
                utils.my_logger.error(f"\tNo Xero ContactID for {member_code}")

print(color(f"Done! 👍🏻", Colors.blue))