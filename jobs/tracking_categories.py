"""
🔹Scheduled job to add accounts of interest that needs to be monitored for totals in DDB
"""

from utils import utils
from colorit import *
import boto3
from decimal import Decimal
from datetime import datetime
import tomllib

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

# ===============================================================
# VARIABLES & CONFIGURATION

since_date = datetime.now().strftime("%Y-01-01")
PARSONAGE_PROJECT_START_DATE = "2022-12-01"
PARSONAGE_TRACKING_ID = '364b0450-d17e-41cf-8211-f8d386fa9264'
BANK_ACCOUNTS = {"DBS": "1000", "NETS": "1001", "Cash": "1002"}

# Load config
with open("tracking_categories.toml", "rb") as f:
    config = tomllib.load(f)

tracking_category_url = f"https://api.xero.com/api.xro/2.0/TrackingCategories/ce1b1125-b513-47de-9649-dd650f2b221e"
_header = {"If-Modified-Since": since_date}
category_options = utils.xero_get(tracking_category_url, **_header)["TrackingCategories"][0]["Options"]
category_options = [x for x in category_options if x["Status"] == "ACTIVE"]
# Remove unwanted keys
for _ in category_options:
    del _['IsDeleted']
    del _['IsArchived']
    del _['IsActive']
    del _['HasValidationErrors']
    del _['Status']
    # Rename keys
    _['id'] = _.pop('TrackingOptionID')

def upload_account_of_interest_tx_to_ddb(list_of_accounts):
    resource = boto3.resource(
        "dynamodb",
        aws_access_key_id=config['srvc_stosc_members']['keys']['STOSC_DDB_ACCESS_KEY_ID'],
        aws_secret_access_key=config['srvc_stosc_members']['keys']['STOSC_DDB_SECRET_ACCESS_KEY'],
        region_name="ap-southeast-1",
    )
    table = resource.Table("stosc_xero_accounts_tracking")
    print(color(f"Inserting {len(list_of_accounts)} records to DDB: {table.name}", Colors.green))
    for _row in list_of_accounts:
        table.put_item(Item=_row)


def update_tracked_accounts_for_invoices():
    print(color(f"================\nChecking Invoices...", Colors.blue))
    has_more_pages = True
    page = 0
    # Go through pages (100 txns per page)
    while has_more_pages:
        page += 1
        url = f"https://api.xero.com/api.xro/2.0/Invoices?Statuses=AUTHORISED,PAID&where=Type%3D%22ACCPAY%22&page={page}"
        # Special Case: Parsonage repairs project started in Dec 2022. Hence only for this item we need to look at items from Dec 2022.
        # Hence overriding.
        _header = {"If-Modified-Since": PARSONAGE_PROJECT_START_DATE}
        txns = utils.xero_get(url, **_header)["Invoices"]
        if len(txns) == 0:
            has_more_pages = False
        else:
            invoices_with_tracking_options = [
                txn for txn in txns if [lineItem for lineItem in txn["LineItems"] if len(lineItem["Tracking"]) > 0]
            ]
            check_tracking_categories(invoices_with_tracking_options)


def update_tracked_accounts_for_member_payments():
    print(color(f"================\nChecking Member Transactions...", Colors.blue))
    for bank_account in BANK_ACCOUNTS.items():
        # Reset page counter for each account (DBS, NETS etc.)
        has_more_pages = True
        page = 0

        # Go through pages (100 txns per page)
        while has_more_pages:
            page += 1
            # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
            url = f'https://api.xero.com/api.xro/2.0/BankTransactions?where=BankAccount.Code=="{bank_account[1]}"&page={page}'
            _header = {"If-Modified-Since": since_date}
            txns = utils.xero_get(url, **_header)["BankTransactions"]
            if len(txns) == 0:
                has_more_pages = False
            else:
                print(color(f"Processing {bank_account[0]}. Page {page}", Colors.blue))
                txns_with_tracking_options = [
                    txn for txn in txns if [lineItem for lineItem in txn["LineItems"] if len(lineItem["Tracking"]) > 0]
                ]
                check_tracking_categories(txns_with_tracking_options)


def check_tracking_categories(txns_with_tracking_options):
    for txn in txns_with_tracking_options:
        for lineItem in txn["LineItems"]:
            # Check if each transaction's (Invoice or payments) line item has any tracking categories
            for lineItem_Tracking in lineItem["Tracking"]:
                for category in category_options:
                    # e.g. Pethrutha (LineItems only return names not TrackingOptionID)
                     if category["Name"] == lineItem_Tracking["Option"]:
                        # We don't want any items for Projects other than 'Parsonage 2022' from last year.
                        # Parsonage project tracking started from Dec 2022
                        if (txn["DateString"] < since_date) and (category["id"] != PARSONAGE_TRACKING_ID):
                            continue
                        if txn['Type'] == 'ACCPAY': 
                            if "expense" in category:
                                # Add to existing entries
                                category["expense"] += Decimal(lineItem["LineAmount"])
                                category["modified_ts"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            else:
                                # First entry
                                category["expense"] = Decimal(lineItem["LineAmount"])
                                category["modified_ts"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        # 'RECEIVE' is for member payments. 'ACCREC' should be for invoices STOSC issues like subscription
                        elif txn['Type'] == 'ACCREC' or txn['Type'] == 'RECEIVE':   
                            if "income" in category:
                                # Add to existing entries
                                category["income"] += Decimal(lineItem["LineAmount"])
                                category["modified_ts"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            else:
                                # First entry
                                category["income"] = Decimal(lineItem["LineAmount"])
                                category["modified_ts"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

if __name__ == '__main__':
    update_tracked_accounts_for_member_payments()
    update_tracked_accounts_for_invoices()
    upload_account_of_interest_tx_to_ddb(category_options)
    