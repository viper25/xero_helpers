import datetime
import utils

# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
from datetime import datetime
import pandas as pd
from datetime import date

eligible_member = []
# For all invoices Updated after since_date i.e. created this year
since_date = datetime.now().strftime("%Y-01-01T00:00:00")
file_name1 = "eligible_gb_members.csv"
file_name2 = "eligible_gb_members_grouped.csv"
todays_date = date.today()
current_month = date.today().month
OVERDUE_LIMIT_DAYS = 182
# IBV-21
INVOICE_YEAR = f"INV-{str(date.today().year)[2:]}"
# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()


def get_eligible_GB_members():
    """
    Get Members that are eligible for GB. Let’s say annual subscription is $600 and if the member has paid $300 which is equal to 6 months. 
    So in Sept his dues are from July to September which is less than 6 months and hence the member is eligible. 
    
    The invoices are checked to see if they were modified at the begining of this year (as they should be when creating new invoices 
    after Jan 1). If this check is not there, we will get all invoices from years past.
    """
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
                    _member["ContactName"] = _invoice["Contact"]["Name"]
                    # _member["ContactID"] = _invoice["Contact"]["ContactID"]1
                    _member["InvoiceNumber"] = _invoice["InvoiceNumber"]
                    _member["Subscription"] = _invoice["Total"]
                    _member["AmountDue"] = _invoice["AmountDue"]

                    # print(color(f"Processing {_member['ContactName']}",Colors.white))

                    if _invoice["Status"] == "PAID":
                        # This member is GB-eligible
                        _member["GBEligible"] = "Yes"
                    elif _invoice["Status"] == "AUTHORISED":
                        if _invoice["Total"] == _invoice["AmountDue"]:
                            _member["GBEligible"] = "No"
                            continue

                        paid_months = (_invoice["Total"] - _invoice["AmountDue"])/(_invoice["Total"]/12)
                        months_outstanding = current_month - paid_months
                        _member["GBEligible"] = "No" if months_outstanding > 6 else "Yes"                        

                        # Loop through all payments save latest payment details
                        for payment in _invoice["Payments"]:
                            _payment_date = utils.parse_Xero_Date(payment["Date"]).date()
                            days_overdue = (todays_date - _payment_date).days
                            # Save the latest payment date
                            if "Days_Overdue" in _member and days_overdue < _member["Days_Overdue"]:
                                _member["Days_Overdue"] = days_overdue
                                _member["Last_Paid_Date"] = _payment_date
                            else:
                                _member["Days_Overdue"] = days_overdue
                                _member["Last_Paid_Date"] = _payment_date

                    # Add this member to list of eligible GB members
                    eligible_member.append(_member)

    print(color(f"Processed {len(eligible_member)} Subscriptions", Colors.orange))
    return eligible_member


def generate_payments_oustanding():
    print(color(f"Generating GB Members ...", Colors.blue))
    # member_invoices_current_year = get_invoices()
    member_payments_current_year = get_eligible_GB_members()
    df_payments = pd.DataFrame(member_payments_current_year)
    # df_payments.to_csv(file_name1, index=False)
    df_grouped_payments = df_payments.groupby(["ContactName", "InvoiceNumber", "Days_Overdue"]).sum().reset_index()
    df_payments.to_csv(file_name1, index=False)

    print("DONE")


if __name__ == "__main__":
    generate_payments_oustanding()
