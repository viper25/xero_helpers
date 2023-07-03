"""
▶ Update a Invoices in DRAFT status with a reference value. Do note: you cannot update a PAID invoice (I think).
▶ Check Tenant IDs in mysecrets.py. If using Demo Tenant, get it's TenantID (Demo accounts TenantID changes)
Use xoauth.exe to get an access token, plug that into xero_first_time.py and get the Demo Company TeenantID and update my_secrets.py
▶ ❗ We assume the subscription amount is the same as last year. Override manually if not so!    
▶ ❗ Set Variables Below 

"""

from colorama import Fore, init
import my_secrets
import utils

# initialize colorama
init(autoreset=True)

# ===============================================================
# VARIABLES & CONFIGURATION
count = 0

# since_date = datetime.now().strftime("%Y-01-01")
since_date = '2020-06-15'

bank_accounts = {"DBS": "1000", "NETS": "1001", "Cash": "1002"}
receive_txns = []
receive_payments = []


def update_invoice(inv):
    url = f"https://api.xero.com/api.xro/2.0/Invoices/{inv['InvoiceID']}"


def updateInvoiceDate(inv):
    global count
    inv_number_yy = inv['InvoiceNumber'].split('-')[1]
    inv_dt_yy = str(utils.parse_Xero_Date(inv['Date']).year - 2000)

    if inv_number_yy != inv_dt_yy:
        # Update the global count variable

        count += 1
        print(
            f"{Fore.WHITE}To Update {inv['InvoiceNumber']} ({Fore.GREEN}{inv['DateString']}) "
            f"{Fore.WHITE} for {inv['Contact']['Name']} "
            f"--> https://invoicing.xero.com/view/{invoice['InvoiceID']}")

        # Set Invoice date (inv['DateString']) to have same year as that of Invoice number (inv['InvoiceNumber']). For
        # e.g. if Invoice number is INV-21-0065, the Invoice Date's year should be the same as the year extracted from
        # Invoice number i.e. 2021

        # Replace the year in the date string
        # print(f"Replacing {inv['DateString']} with {'20' + inv_number_yy + inv['DateString'][4:]}")
        inv['DateString'] = '20' + inv_number_yy + inv['DateString'][4:]

        update_invoice(inv)


# Just a failsafe check
if my_secrets.xero_tenant_ID == 'f7dc56b9-fe29-43cf-be0a-a5488da4e30f':
    print(f"{Fore.RED}CAREFUL!: This is STOSC PRODUCTION ACCOUNT. Are you sure?")
    # sys.exit(0)

has_more_pages = True
page = 0

# Go through pages (100 txns per page)
while has_more_pages:
    page += 1
    url = f'https://api.xero.com/api.xro/2.0/Invoices?where=Type="ACCREC"&Statuses=AUTHORISED&summaryOnly=True&page={page}'
    _header = {'If-Modified-Since': since_date}
    invoices = utils.xero_get(url, **_header)
    if len(invoices['Invoices']) == 0:
        has_more_pages = False
    else:
        for invoice in invoices['Invoices']:
            if (invoice['InvoiceNumber'].startswith('INV') \
                    or invoice['InvoiceNumber'].startswith('HF-')):
                updateInvoiceDate(invoice)

print(f"{Fore.BLUE}{count} Invoices")
