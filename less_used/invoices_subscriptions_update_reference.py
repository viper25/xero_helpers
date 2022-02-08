"""
▶ Update a Invoices in DRAFT status with a reference value. Do note: you cannot update a PAID invoice (I think).
▶ Check Tenant IDs in mysecrets.py. If using Demo Tenant, get it's TenantID (Demo accounts TenantID changes)
Use xoauth.exe to get an access token, plug that into xero_first_time.py and get the Demo Company TeenantID and update my_secrets.py
▶ ❗ We assume the subscription amount is the same as last year. Override manually if not so!    
▶ ❗ Set Variables Below 

"""

import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import my_secrets
from datetime import datetime
import pandas as pd

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# ===============================================================
# VARIABLES & CONFIGURATION

since_date = datetime.now().strftime("%Y-01-01")
#since_date = '2020-06-15'

bank_accounts = {"DBS":"1000","NETS":"1001","Cash":"1002"}
receive_txns = []
receive_payments = []

def updateInvoiceReference(ref):
    utils.my_logger.info(f"Updating Invoice Reference to '{ref}'\n")
    pass

# Just a failsafe check
if my_secrets.xero_tenant_ID == 'XXX':
    print(color(f"CAREFUL!: This is STOSC PRODUCTION ACCOUNT. Are you sure?",Colors.red))
    print(color(f"Did you set NEXT Invoice Numbers? to INV-22-001? ",Colors.red))
    sys.exit(0)

utils.my_logger.info(f"Processing Member Subscriptions\n================",Colors.blue)
has_more_pages = True
page = 0

# Go through pages (100 txns per page)
while has_more_pages:
    page += 1
    # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
    url = f'https://api.xero.com/api.xro/2.0/Payments?where=PaymentType="ACCRECPAYMENT"&page={page}'
    _header = {'If-Modified-Since': since_date}
    payments = utils.xero_get(url,**_header)
    if len(payments['Payments']) == 0:
        has_more_pages = False
    else:
        for _payments in payments['Payments']:
            # Paid invoices without a Reference will not have the Reference field.
            utils.my_logger.info(f"For Invoice {_payments['Invoice']['InvoiceNumber']}. [https://invoicing.xero.com/view/{_payments['Invoice']['InvoiceID']}]")
            if _payments['Status'] == 'AUTHORISED' and _payments['Reference']=='':
                if _payments['Invoice']['InvoiceNumber'].startswith('INV-21'):
                    updateInvoiceReference('Subscription 2021')
                elif _payments['Invoice']['InvoiceNumber'].startswith('INV-20'):
                    updateInvoiceReference('Subscription 2020')
                elif _payments['Invoice']['InvoiceNumber'].startswith('INV-19'):
                    updateInvoiceReference('Subscription 2019')
                elif _payments['Invoice']['InvoiceNumber'].startswith('INV-18'):
                    updateInvoiceReference('Subscription 2018')
                elif _payments['Invoice']['InvoiceNumber'].startswith('INV-17'):
                    updateInvoiceReference('Subscription 2017')


print(color(f"Done! 👍🏻",Colors.blue))                  