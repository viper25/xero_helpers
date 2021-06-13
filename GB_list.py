from datetime import date
import datetime

import sqlalchemy
import utils

# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
from datetime import datetime
import pandas as pd
import logging
import enum
from sqlalchemy import create_engine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

_user = "stosc_ro"
_password = os.environ.get("STOSC_DB_PWD")
_host = os.environ.get("STOSC_DB_HOST")

class Databases(enum.Enum):
    CRM = "stosc_churchcrm"
    FORMS = "forms_db"

receive_payments = []
# For all invoices Updated after since_date i.e. created this year
since_date = datetime.now().strftime("%Y-01-01")
# since_date = '2021-06-01'
file_name = "gb_raw.csv"
# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# Load a pre-prepared Xero contacts extract. This was prepared by generate_Xero_Contact_List.py
df_xero_contacts = pd.read_csv('xero_contacts.csv')     

def getActiveMembers():
    sql = "SELECT"
    sql += " family_custom.c7 as FamilyCode,"
    sql += " per_Gender as Gender,"
    sql += " CONCAT(per_FirstName,' ',per_LastName) as MemberName"
    sql += " FROM person_per"
    sql += " INNER JOIN family_fam ON family_fam.fam_ID = person_per.per_fam_ID"
    sql += " and person_per.per_fmr_ID in (1,2) AND person_per.per_cls_ID <> 4"
    sql += " AND family_fam.fam_DateDeactivated is null"
    sql += " AND person_per.per_id not in (select r2p_record_id from record2property_r2p where record2property_r2p.r2p_pro_ID = 12)"
    sql += " INNER JOIN family_custom ON family_custom.fam_ID = person_per.per_fam_ID"
    sql += " ORDER BY family_custom.c7;"

    db_connection_str = f'mysql+pymysql://{_user}:{_password}@{_host}/{Databases.CRM.value}'
    db_connection = sqlalchemy.create_engine(db_connection_str)
    df = pd.read_sql(sql, con=db_connection)
    return df

def get_Contact_memberID(contactID):
    if not df_xero_contacts.loc[df_xero_contacts['ContactID'] ==contactID].empty:
        return df_xero_contacts.loc[df_xero_contacts['ContactID'] ==contactID]['memberCode'].item()
    else:
        return "User Not Found"

def getInvoiceAmount(invoiceID):
    url = f"https://api.xero.com/api.xro/2.0/Invoices/{invoiceID}"
    invoice = utils.xero_get(url)
    return "Not Implemented"

def get_member_invoice_payments(since_date):
    has_more_pages = True
    page = 0

    # Go through pages (100 txns per page)
    while has_more_pages:
        page += 1
        print(color(f"  Processing Page {page} of payments...", Colors.orange))
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
                    "FamilyName": _invoice["Contact"]["Name"],
                    "FamilyCode": get_Contact_memberID(_invoice["Contact"]["ContactID"]),
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
    print(color(f"  Processed {len(receive_payments)} Subscriptions", Colors.orange))
    return receive_payments

print(color(f"Getting Payments...", Colors.white))
list_invoice_payments = get_member_invoice_payments(since_date)
print(color(f"Getting Active Member List...", Colors.white))
df_active_members = getActiveMembers()
df_payments = pd.DataFrame(list_invoice_payments)
print(color(f"Joining the two...", Colors.white))
df_merged = pd.merge(df_payments,df_active_members,on='FamilyCode')


print(color(f"ACTIVE MEMBERS:\n---------------{df_active_members.head(2)}\n==========================", Colors.blue))
print(color(f"PAYMENTS:\n---------------{df_payments.head(2)}\n==========================", Colors.blue))
print(color(f"MERGED:\n---------------{df_merged.head(2)}\n==========================", Colors.blue))

df_merged.to_csv(file_name, index=False)
print(color(f"Written to {file_name}", Colors.white))

print("DONE")
