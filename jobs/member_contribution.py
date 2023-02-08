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

import utils

# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import pandas as pd
import numpy as np
import boto3
from decimal import Decimal
import my_secrets
from datetime import datetime

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# ===============================================================
# VARIABLES & CONFIGURATION

since_date = datetime.now().strftime("%Y-01-01")
# since_date = '2021-01-01'

bank_accounts = {"DBS": "1000", "NETS": "1001", "Cash": "1002"}
receive_txns = []
received_payments = []
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
            "Holy Week Donation",
            "Christmas Offering",
            "Diocesan Development Fund",
            "Metropolitan Fund ",
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
            "Kohne Sunday"
        ],
        "AccountCode": [
            "3010",
            "3020",
            "3030",
            "3040",
            "3050",
            "3060",
            "3070",
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
            "3310"
        ],
        "Total": [0] * 26
    }
)

# Certain accounts to be monitored for display in Bot e.g. "Vanitha Dinam"
accounts_of_interest = [
    {"AccountCode": "3240", "AccountName": "Vanitha Dinam", "keyword": "Vanitha Dinam", "Total": 0},
    {"AccountCode": "3100", "AccountName": "Liturgy Calendar", "keyword": "Liturgy", "Total": 0},
    {"AccountCode": "3240", "AccountName": "Snehasparsham", "keyword": "Snehasparsham", "Total": 0},
    {"AccountCode": "3240", "AccountName": "Pethrutha", "keyword": "Pethrutha", "Total": 0},
    {"AccountCode": "3240", "AccountName": "Migrant Workers", "keyword": "Migrant", "Total": 0},
    {"AccountCode": "3180", "AccountName": "Youth Car Wash", "keyword": "Car Wash", "Total": 0}
    # {"AccountCode": "5170", "AccountName": "Altar Renovation", "keyword": "Altar Renovation", "Total": 0}
]

df_members = pd.read_csv("csv\\xero_contacts.csv")

write_to_csv = False
# ===============================================================


def upload_member_tx_to_ddb(df_records):
    resource = boto3.resource(
        "dynamodb",
        aws_access_key_id=my_secrets.DDB_ACCESS_KEY_ID,
        aws_secret_access_key=my_secrets.DDB_SECRET_ACCESS_KEY,
        region_name="ap-southeast-1",
    )
    table = resource.Table("stosc_xero_member_payments")
    print(color(f"Inserting {len(df_records)} records to DDB: {table.name}", Colors.green))
    for index, row in df_records.iterrows():
        chunk = {
            "ContactID": row[0],
            "ContactName": row[1],
            "AccountCode": f"{row[4]}_{row[2]}",
            "Account": row[3],
            "LineAmount": Decimal(str(row[5])),
            "modfied_ts": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        table.put_item(Item=chunk)


def upload_account_of_interest_tx_to_ddb(list_of_accounts):
    resource = boto3.resource(
        "dynamodb",
        aws_access_key_id=my_secrets.DDB_ACCESS_KEY_ID,
        aws_secret_access_key=my_secrets.DDB_SECRET_ACCESS_KEY,
        region_name="ap-southeast-1",
    )
    # TODO Truncate the table before inserting
    table = resource.Table("stosc_xero_accounts_of_interest")
    print(color(f"Inserting {len(list_of_accounts)} records to DDB: {table.name}", Colors.green))
    for _row in list_of_accounts:
        table.put_item(Item=_row)


# Operations on the Transactions DataFrame
def cleanup_txns_df(_df_tnxs):
    # Explode the Line Items col so that there's one ROW per Line Item.
    _df_tnxs = _df_tnxs.explode("Line Items")

    # Add the columns from exploded rows
    _df_tnxs["AccountCode"] = _df_tnxs["Line Items"].apply(lambda x: x.get("AccountCode"))
    _df_tnxs["LineAmount"] = _df_tnxs["Line Items"].apply(lambda x: x.get("LineAmount"))

    # Remove unwanted exploded dict col
    _df_tnxs = _df_tnxs.drop(columns=["Line Items", "BankAccount", "Net Amount"])

    return _df_tnxs

def get_member_ID(_str_name):
    # Get the member ID from the name
    if len(df_members.loc[df_members['ContactID'] == _str_name]) == 0:
        _member_code = 'NA'
    else:
        _member_code = df_members.loc[df_members['ContactID'] == _str_name].iloc[0][0]
    return _member_code


# https://api-explorer.xero.com/accounting/banktransactions/getbanktransactions?query-where=BankAccount.Code%3D%3D%221000%22&query-page=1&header-if-modified-since=2021-04-20
def get_member_txns(since_date):

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
            _header = {"If-Modified-Since": since_date}
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
                        # Nested dict
                        "Line Items": _txn["LineItems"],
                        "Net Amount": _txn["Total"],
                        "Status": _txn["Status"],
                    }
                    for _txn in txns["BankTransactions"]
                    if (
                        # Only those tnxs that are payments to STOSC
                        _txn["Type"] == "RECEIVE"
                        and _txn["Status"] == "AUTHORISED"
                        and _txn["IsReconciled"] == True
                    )
                ]
                receive_txns.extend(_receive_txns)

                # Track accounts of interest
                for _txn in txns["BankTransactions"]:
                    if (
                        # Only those tnxs that are payments to STOSC
                        _txn["Type"] == "RECEIVE"
                        and _txn["Status"] == "AUTHORISED"
                        and _txn["IsReconciled"] == True
                    ):
                        # Build the member payments matrix
                        _receive_txns = {
                            # Build the output item
                            "ContactID": _txn["Contact"]["ContactID"],
                            "ContactName": _txn["Contact"]["Name"],
                            "MemberID": get_member_ID(_txn["Contact"]["ContactID"]),
                            "BankAccount": _txn["BankAccount"]["Name"],
                            # "Year": _txn['DateString'].split('-')[0],
                            "Year": str(utils.parse_Xero_Date(_txn["Date"]).year),
                            # Nested dict
                            "Line Items": _txn["LineItems"],
                            "Net Amount": _txn["Total"],
                            "Status": _txn["Status"],
                        }
                        # Loop through each line item and see if it matches any "accounts of interest"
                        for lineItem in _txn["LineItems"]:
                            for account in accounts_of_interest:
                                if (
                                    account["AccountCode"] == lineItem["AccountCode"]
                                    and account["keyword"].upper() in lineItem["Description"].strip().upper()
                                ):
                                    # Update Total
                                    account['Total'] += Decimal(lineItem["LineAmount"])
                                    account["modfied_ts"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return receive_txns


# https://api-explorer.xero.com/accounting/payments/getpayments?query-page=1&query-where=PaymentType%3D%22ACCRECPAYMENT%22&header-if-modified-since=2021-04-25
def get_member_invoice_payments(since_date):
    print(color(f"Processing Member Subscriptions\n================", Colors.blue))
    has_more_pages = True
    page = 0

    # Go through pages (100 txns per page)
    while has_more_pages:
        page += 1
        # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
        url = f'https://api.xero.com/api.xro/2.0/Payments?where=PaymentType="ACCRECPAYMENT"&page={page}'
        _header = {"If-Modified-Since": since_date}
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
                )
            ]
            received_payments.extend(_received_payments)
    return received_payments


list_invoice_payments = get_member_invoice_payments(since_date)
list_all_txns = get_member_txns(since_date)

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

df_grouped = df_merged.groupby(["ContactID", "ContactName", "MemberID", "AccountCode", "Account", "Year"]).sum().reset_index()
print(color(df_grouped.sort_values(by=["ContactName"]).head(5), (200, 200, 200)))
if write_to_csv:
    df_grouped.to_csv("csv\member_contributions_grouped.csv", index=True)
# df_grouped.pivot_table(index=["ContactName","Account"]).to_csv('member_contributions_grouped-1.csv',index=True)

# Ref: https://pbpython.com/pandas-pivot-table-explained.html
# Pivot to show all Accounts in cols
# The values column automatically averages the data so should change to sum.
df_pivoted = df_grouped.pivot_table(index=["ContactName","Year","MemberID"], columns="Account", values="LineAmount", aggfunc=np.sum, fill_value=0)
if write_to_csv:
    df_pivoted.to_csv("csv\member_contributions_pivoted.csv", index=True)

upload_account_of_interest_tx_to_ddb(accounts_of_interest)
upload_member_tx_to_ddb(df_grouped)

print(background(color(f"Done", (0, 0, 0)), Colors.green))
