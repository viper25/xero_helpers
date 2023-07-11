"""
🔹To get a matrix of all the members contributions for the year (Excel output) 
🔹Scheduled job to update member payments in DDB
🔹Scheduled job to add accounts of interest that needs to be monitored for totals in DDB

This does NOT include 
Invoice payments (i.e. member subscription payments)
https://developer.xero.com/documentation/api/banktransactions#GET
Up to 100 bank transactions will be returned per call, with line items shown for each transaction, 
when the page parameter is used e.g. page=1. The data is refreshed in DDB which is used by the Telegram bot 
"""

# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import pandas as pd
import numpy as np
import boto3
from decimal import Decimal
import my_secrets
from datetime import datetime
import os
import utils

init_colorit()

# ===============================================================
# VARIABLES & CONFIGURATION

# Get all data from this date on. This will reduce the amount of data to fetch from Xero.
# Get from the beginning of the previous year
XERO_GET_DATA_SINCE_DATE = datetime(datetime.now().year - 1, 1, 1).strftime("%Y-%m-%d")
UPDATE_TX_FOR_YEAR = datetime.now().year

bank_accounts = {"DBS": "1000", "NETS": "1001", "Cash": "1002"}
receive_txns = []
received_payments = []
tracking_categories = {
    "'ce1b1125-b513-47de-9649-dd650f2b221e'": 'Parsonage 2022'
}
accounts_lookup = pd.DataFrame(
    {
        "label": [
            "Member Subscription",
            "Offertory",
            "Holy Qurbana",
            "Auction Sales",
            "Birthday Offering",
            "Baptism & Wedding Offering",
            "Catholicate Fund Donation",
            "Cathedral Fellowship",
            "Holy Week Donation",
            "Christmas Offering",
            "Diocesan Development Fund",
            "Metropolitan Fund",
            "Resisa Donation",
            "Self Denial Fund",
            "Marriage Assistance Fund",
            "Seminary Fund",
            "Mission Fund",
            "Sunday School",
            "Youth Fellowship",
            "Tithe",
            "Thanksgiving Auction",
            "Thanksgiving Donation",
            "Other Revenue",
            "Interest Income",
            "St. Mary's League Income",
            "Donations & Gifts",
            "Kohne Sunday",
            "Snehasparsham & Vanitha Dinam"
        ],
        "AccountCode": [
            "3010",
            "3020",
            "3030",
            "3040",
            "3050",
            "3060",
            "3070",
            "3260",
            "3080",
            "3090",
            "3100",
            "3110",
            "3120",
            "3130",
            "3140",
            "3150",
            "3160",
            "3170",
            "3180",
            "3190",
            "3200",
            "3210",
            "3220",
            "3230",
            "3240",
            "3250",
            "3310",
            "3320",
        ],
        "Total": [0] * 28
    }
)

df_members = pd.read_csv(f"csv{os.sep}xero_contacts.csv")

write_to_csv = False


# ===============================================================


def upload_member_tx_to_ddb(records: dict):
    resource = boto3.resource(
        "dynamodb",
        aws_access_key_id=my_secrets.DDB_ACCESS_KEY_ID,
        aws_secret_access_key=my_secrets.DDB_SECRET_ACCESS_KEY,
        region_name="ap-southeast-1",
    )
    table = resource.Table("stosc_xero_member_payments")
    print(color(f"Inserting {len(records)} records to DDB: {table.name}", Colors.green))
    for record in records:
        chunk = {
            "ContactID": record["ContactID"],
            "ContactName": record["ContactName"],
            "AccountCode": f"{record['Year']}_{record['AccountCode']}",
            "Account": record["Account"],
            "LineAmount": Decimal(str(record["LineAmount"])),
            "modfied_ts": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        table.put_item(Item=chunk)


# Operations on the Transactions DataFrame
def cleanup_txns_df(_df_tnxs):
    # Explode the Line Items col so that there's one ROW per Line Item.
    _df_tnxs = _df_tnxs.explode("Line Items")

    # Add the columns from exploded rows
    _df_tnxs["AccountCode"] = _df_tnxs["Line Items"].apply(lambda x: x.get("AccountCode"))
    _df_tnxs["LineAmount"] = _df_tnxs["Line Items"].apply(lambda x: x.get("LineAmount"))

    # Remove unwanted exploded dict col
    _df_tnxs = _df_tnxs.drop(columns=["Line Items", "BankAccount", "Net Amount", "Status"])

    return _df_tnxs


def get_member_ID(_str_name):
    # Get the member ID from the name
    if len(df_members.loc[df_members['ContactID'] == _str_name]) == 0:
        _member_code = 'NA'
    else:
        _member_code = df_members.loc[df_members['ContactID'] == _str_name].iloc[0][0]
    return _member_code


# https://api-explorer.xero.com/accounting/banktransactions/getbanktransactions?query-where=BankAccount.Code%3D%3D%221000%22&query-page=1&header-if-modified-since=2021-04-20
def get_member_txns():
    print(color(f"\nProcessing Member Transactions\n================", Colors.blue))
    for bank_account in bank_accounts.items():
        # Reset page counter for each account (DBS, NETS etc.)
        has_more_pages = True
        page = 0

        # Go through pages (100 txns per page)
        while has_more_pages:
            page += 1
            # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
            url = f'https://api.xero.com/api.xro/2.0/BankTransactions?where=BankAccount.Code=="{bank_account[1]}"&page={page}'
            _header = {"If-Modified-Since": XERO_GET_DATA_SINCE_DATE}
            txns = utils.xero_get(url, **_header)
            if len(txns["BankTransactions"]) == 0:
                has_more_pages = False
            else:
                print(color(f"Processing {bank_account[0]}. Page {page}", Colors.blue))
                # Keep only "Type":"RECEIVE" & construct a dict via Python List Comprehension
                _receive_txns = [
                    {
                        # Build the output item
                        "ContactID": _txn["Contact"]["ContactID"],
                        "ContactName": _txn["Contact"]["Name"],
                        "MemberID": get_member_ID(_txn["Contact"]["ContactID"]),
                        "BankAccount": _txn["BankAccount"]["Name"],
                        # "Year": _txn['DateString'].split('-')[0],
                        "Year": str(utils.parse_Xero_Date(_txn["Date"]).year),
                        "Line Items": _txn["LineItems"],  # Nested dict
                        "Net Amount": _txn["Total"],
                        "Status": _txn["Status"],
                    }
                    for _txn in txns["BankTransactions"]
                    if (
                            # Only those tnxs that are payments to STOSC
                            _txn["Type"] == "RECEIVE"
                            and _txn["Status"] == "AUTHORISED"
                            and _txn["IsReconciled"] == True
                            # Get tx only for current year
                            and utils.parse_Xero_Date(_txn["Date"]).year == UPDATE_TX_FOR_YEAR
                    )
                ]
                receive_txns.extend(_receive_txns)
    return receive_txns


# https://api-explorer.xero.com/accounting/payments/getpayments?query-page=1&query-where=PaymentType%3D%22ACCRECPAYMENT%22&header-if-modified-since=2021-04-25
def get_member_invoice_payments():
    print(color(f"\nProcessing Member Subscriptions\n================", Colors.blue))
    has_more_pages = True
    page = 0

    # Go through pages (100 txns per page)
    while has_more_pages:
        page += 1
        # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
        url = f'https://api.xero.com/api.xro/2.0/Payments?where=PaymentType="ACCRECPAYMENT"&page={page}'
        _header = {"If-Modified-Since": XERO_GET_DATA_SINCE_DATE}
        payments = utils.xero_get(url, **_header)
        if len(payments["Payments"]) == 0:
            has_more_pages = False
        else:
            # Keep only "Type":"RECEIVE" & construct a dict via Python List Comprehension
            _received_payments = [
                {
                    # Build the output item
                    "ContactID": _payments["Invoice"]["Contact"]["ContactID"],
                    "ContactName": _payments["Invoice"]["Contact"]["Name"],
                    "MemberID": get_member_ID(_payments["Invoice"]["Contact"]["ContactID"]),
                    # We assume any invoices not starting with INV is issued for harvest Festival
                    "AccountCode": "3010" if _payments["Invoice"]["InvoiceNumber"].startswith("INV") else "3200",
                    # "Year": _txn['DateString'].split('-')[0],
                    "Year": str(utils.parse_Xero_Date(_payments["Date"]).year),
                    "LineAmount": _payments["Amount"],
                }
                for _payments in payments["Payments"]
                if (
                        # Only those tnxs that are payments to STOSC
                        _payments["Status"] == "AUTHORISED"
                        and _payments["IsReconciled"] == True
                        and utils.parse_Xero_Date(_payments["Date"]).year == UPDATE_TX_FOR_YEAR
                )
            ]
            received_payments.extend(_received_payments)
    return received_payments


list_invoice_payments = get_member_invoice_payments()
list_all_txns = get_member_txns()

# Make DataFrames
df_tnxs = pd.DataFrame(list_all_txns)
df_payments = pd.DataFrame(list_invoice_payments)

df_tnxs = cleanup_txns_df(df_tnxs)

# Find a contact
# df_tnxs.loc[df_tnxs['ContactName'] == "Vibin Joseph Kuriakose"]

# Merge Subscription Payments and Transaction Data Frames
df_merged = pd.concat([df_payments, df_tnxs])

# Lookup and Account code and Add Account Desc
s = accounts_lookup.set_index("AccountCode")["label"]
df_merged["Account"] = df_merged["AccountCode"].map(s)

# Save to CSV
if write_to_csv:
    df_merged.to_csv("csv\member_contributions.csv", index=False)

# Group by Contacts to show all payments from a member
'''
TODO:
FutureWarning: The default value of numeric_only in DataFrameGroupBy.sum is deprecated. In a future version, 
numeric_only will default to False. Either specify numeric_only or select only columns which should be valid for the function.
'''

df_grouped = df_merged.groupby(
    ["ContactID", "ContactName", "MemberID", "AccountCode", "Account", "Year"]).sum().reset_index()
print(color(df_grouped.sort_values(by=["ContactName"]).head(5), (200, 200, 200)))
if write_to_csv:
    df_grouped.to_csv("csv\member_contributions_grouped.csv", index=True)
# df_grouped.pivot_table(index=["ContactName","Account"]).to_csv('member_contributions_grouped-1.csv',index=True)

# Ref: https://pbpython.com/pandas-pivot-table-explained.html
# Pivot to show all Accounts in cols
# The values column automatically averages the data so should change to sum.
df_pivoted = df_grouped.pivot_table(index=["ContactName", "Year", "MemberID"], columns="Account", values="LineAmount",
                                    aggfunc=np.sum, fill_value=0)
if write_to_csv:
    df_pivoted.to_csv("csv\member_contributions_pivoted.csv", index=True)

list_of_records = df_grouped.to_dict(orient='records')
upload_member_tx_to_ddb(list_of_records)

print(background(color(f"Done", (0, 0, 0)), Colors.green))
