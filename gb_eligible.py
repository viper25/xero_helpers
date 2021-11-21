"""
As of GB Date if they have dues of > 6 months they are not eligible

Get Members that are eligible for GB. Let’s say annual subscription is $600 and if the member has paid $300 which is equal to 6 months. 
So in Sept his dues are from July to September which is less than 6 months and hence the member is eligible. 

The invoices are checked to see if they were modified at the begining of this year (as they should be when creating new invoices 
after Jan 1). If this check is not there, we will get all invoices from years past.
"""
import datetime
import utils

# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
from datetime import datetime
import pandas as pd
from datetime import date

all_members = []
# For all invoices Updated after since_date i.e. created this year
since_date = datetime.now().strftime("%Y-01-01T00:00:00")
file_eligible_gb_members = "csv\\eligible_gb_members.csv"
file_eligible_gb_members_grouped = "csv\\eligible_gb_members_grouped.csv"
file_members = "csv\\contacts1.txt"
todays_date = date.today()
current_month = date.today().month
OVERDUE_LIMIT_DAYS = 182
# INV-21
INVOICE_YEAR = f"INV-{str(date.today().year)[2:]}"
# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

'''
Ensure this file is already generated
'''
def get_member_code(name):
    df = pd.read_csv(file_members)
    try:
        code = df[df["Name"] == name]['memberCode'].iloc[0]
    except:
        code = "" 
    return code


def get_eligible_GB_members():
    has_more_pages = True
    page = 0

    # Go through pages (100 txns per page)
    while has_more_pages:
        page += 1
        # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
        url = f"https://api.xero.com/api.xro/2.0/Invoices?Statuses=AUTHORISED,PAID&page={page}"
        _header = {"If-Modified-Since": since_date}
        invoices = utils.xero_get(url, **_header)
        if len(invoices["Invoices"]) == 0:
            has_more_pages = False
        else:
            for _invoice in invoices["Invoices"]:
                if _invoice["Type"] == "ACCREC" and _invoice["InvoiceNumber"].startswith(INVOICE_YEAR):
                    # Reset member dict
                    _member = {}
                    _member["Member_Name"] = _invoice["Contact"]["Name"]
                    _member["Member_Code"] = get_member_code(_invoice["Contact"]["Name"])
                    print(color(f"Processing {_invoice['Contact']['Name']}", Colors.orange))
                    # _member["ContactID"] = _invoice["Contact"]["ContactID"]1
                    _member["Invoice_Number"] = _invoice["InvoiceNumber"]
                    _member["Subscription"] = _invoice["Total"]
                    _member["Amount_Due"] = _invoice["AmountDue"]

                    # print(color(f"Processing {_member['ContactName']}",Colors.white))

                    if _invoice["Status"] == "PAID":
                        # This member is GB-eligible
                        _member["GB_Eligible"] = "Yes"
                    elif _invoice["Status"] == "AUTHORISED":
                        if _invoice["Total"] == _invoice["AmountDue"]:
                            _member["GB_Eligible"] = "No"
                            all_members.append(_member)
                            continue

                        months_paid_for = (_invoice["Total"] - _invoice["AmountDue"])/(_invoice["Total"]/12)
                        months_unpaid = current_month - months_paid_for
                        _member["Months_Paid_For"] = months_paid_for
                        _member["Months_Unpaid"] = months_unpaid
                        months_outstanding = 12 - months_paid_for
                        _member["GB Eligible"] = "No" if months_outstanding > 6 else "Yes"                        

                        # Loop through all payments save latest payment details
                        for payment in _invoice["Payments"]:
                            _payment_date = utils.parse_Xero_Date(payment["Date"]).date()
                            days_overdue = (todays_date - _payment_date).days
                            # months_paid_for = (_invoice["Total"]-_invoice["AmountDue"])/(_invoice["Total"]/12)
                            
                            # Save the latest payment date
                            if "Days_Overdue" in _member and days_overdue < _member["Days_Overdue"]:
                                _member["Days_Since_Last_Payment"] = days_overdue
                                _member["Last_Paid_Date"] = _payment_date
                            else:
                                _member["Days_Since_Last_Payment"] = days_overdue
                                _member["Last_Paid_Date"] = _payment_date

                    # Add this member to list of eligible GB members
                    all_members.append(_member)

    print(color(f"Processed {len(all_members)} Subscriptions", Colors.orange))
    return all_members


def generate_payments_oustanding():
    print(color(f"Generating GB Members ...", Colors.blue))
    # member_invoices_current_year = get_invoices()
    member_payments_current_year = get_eligible_GB_members()
    df_payments = pd.DataFrame(member_payments_current_year).sort_values(by=["Member_Name"])
    # df_payments.to_csv(file_name1, index=False)
    # df_grouped_payments = df_payments.groupby(["ContactName", "InvoiceNumber", "Days_Since_Last_Payment"]).sum().reset_index()
    df_payments.to_csv(file_eligible_gb_members, index=False)
    # df_grouped_payments.to_csv(file_eligible_gb_members_grouped, index=False)

if __name__ == "__main__":
    generate_payments_oustanding()
    print("DONE")
