"""
To get a matrix of all the members contributions for the year
https://developer.xero.com/documentation/api/banktransactions#GET
https://api-explorer.xero.com/accounting/banktransactions/getbanktransactions?query-where=BankAccount.Code%3D%3D%221000%22&query-page=1&header-if-modified-since=2021-04-20
Up to 100 bank transactions will be returned per call, with line items shown for each transaction, when the page parameter is used e.g. page=1
"""

import requests
import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *
import csv
import pandas as pd

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

since_date = '2021-04-10'
accounts = {"DBS":"1000","NETS":"1001","Cash":"1002"}
receive_txns = []

def get_member_txns(since_date):
    _member_txns = {}
    for account in accounts.items():
        # Reset page counter for each account (DBS, NETS etc.)
        has_more_pages = True
        page = 0
        
        # Go through pages (100 txns per page)
        while has_more_pages:
            page += 1
            url = f'https://api.xero.com/api.xro/2.0/BankTransactions?where=BankAccount.Code=="{account[1]}"&page={page}'
            _header = {'If-Modified-Since': since_date}
            txns = utils.xero_get(url,**_header)
            if len(txns['BankTransactions']) == 0:
                has_more_pages = False
            else:
                print(color(f"Processing {account[0]}. Page {page}",Colors.blue))
                # Keep only "Type":"RECEIVE" & construct a dict via Python List Comprehension
                _receive_txns = [
                    {
                        # Build the output item
                        "ContactID": _txn['Contact']['ContactID'],
                        "Name": _txn['Contact']['Name'],                        
                        "Account": _txn['BankAccount']['Name'],
                        "Date": _txn['DateString'],
                        # Nested dict
                        "Line Items": _txn['LineItems'],
                        "Net Amount": _txn['Total']
                    } 
                    for _txn in txns['BankTransactions'] 
                    if (
                        # Only those tnxs that are payments to STOSC
                        _txn['Type'] == 'RECEIVE' and 
                        _txn['IsReconciled'] == True
                        )]
                receive_txns.extend(_receive_txns)
        
    return receive_txns

list_all_txns = get_member_txns(since_date)

# Explode the Line Items col so that there's one ROW per item.
df = pd.DataFrame(list_all_txns)
print(df.head(5))
df = df.explode('Line Items')

# Add the columns from exploded rows
df["LineItem"] = df["Line Items"].apply(lambda x: x.get('Description'))
df["LineAmount"] = df["Line Items"].apply(lambda x: x.get('LineAmount'))
df["AccountCode"] = df["Line Items"].apply(lambda x: x.get('AccountCode'))

# Remove unwanted dict col
df = df.drop(columns=["Line Items"])

df.to_csv('member_contributions.csv',index=False)

print(
    background(
        color(f"Done",(0,0,0)),Colors.green
        )
    )
