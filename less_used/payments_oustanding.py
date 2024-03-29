from utils import utils

# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
from datetime import datetime
import pandas as pd

receive_payments = []
# For all invoices Updated after since_date i.e. created this year
since_date = datetime.now().strftime("%Y-01-01")
file_name = "payments_oustanding.csv"
# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

def get_member_invoice_payments(since_date):
    """
    Get Invoices that are named `INV-20` where 20 represents the year.
    Only check where Invoice status = AUTHORISED,PAID and startswith('INV'). 
    The invoices are checked to see if they were modified at the begining of 
    this year (as they should be when creating new invoices after Jan 1). 
    If this check is not there, we will get all invoices from years past.
    """
    has_more_pages = True
    page = 0

    # Go through pages (100 txns per page)
    while has_more_pages:
        page += 1
        # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
        url = f'https://api.xero.com/api.xro/2.0/Invoices?page={page}&where=Type=="ACCREC"&Statuses=AUTHORISED,PAID&summaryonly=True'
        _header = {"If-Modified-Since": since_date}
        invoices = utils.xero_get(url, **_header)
        if len(invoices["Invoices"]) == 0:
            has_more_pages = False
        else:
            # Keep only "Type":"RECEIVE" & construct a dict via Python List Comprehension
            _invoices = [
                {
                    # Build the output item
                    "ContactName": _invoice["Contact"]["Name"],
                    "InvoiceNumber": _invoice["InvoiceNumber"],
                    "InvoiceDate": utils.parse_Xero_Date(_invoice["Date"]).date(),
                    "InvoiceYear": "20" + _invoice["InvoiceNumber"][4:][:2],
                    "Total": _invoice["Total"],
                    "AmountDue": _invoice["AmountDue"],
                    "AmountPaid": _invoice["AmountPaid"],
                }
                for _invoice in invoices["Invoices"]
                if (
                    # Only Subscription invoices and No Harvest Festival ones
                    _invoice["InvoiceNumber"].startswith("INV")
                )
            ]
            receive_payments.extend(_invoices)
    print(color(f"Processed {len(receive_payments)} Subscriptions", Colors.orange))
    return receive_payments


def generate_payments_oustanding():
    print(color(f"Oustanding Payments csv generator", Colors.blue))
    list_invoice_payments = get_member_invoice_payments(since_date)
    df_payments = pd.DataFrame(list_invoice_payments)
    df_payments.to_csv(file_name, index=False)
    print(color(f"Written to {file_name}", Colors.blue))

    print("DONE")


if __name__ == "__main__":
    generate_payments_oustanding()
