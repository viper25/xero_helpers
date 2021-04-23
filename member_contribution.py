"""
To get a matrix of all the members contributions for the year. This does NOT include 
Invoice payments (i.e. member subscription payments)
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
import numpy as np

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

since_date = '2021-01-01'
bank_accounts = {"DBS":"1000","NETS":"1001","Cash":"1002"}
receive_txns = []
lookup = pd.DataFrame({
    'label':[
        "Member Subscription","Offertory","Holy Qurbana","Auction Sales","Birthday Offering","Baptism and wedding Offering","Catholicate Fund Donation","Good Friday Donation","Christmas Offering","Diocesan Development Fund","Metropolitan Fund ","Resisa Donation","Self Denial Fund","Marriage Assistance Fund","Seminary Fund","Mission Fund","Sunday School","Youth Fellowship Donations","Tithe","Annual Thanksgiving Auction","Annual Thanksgiving Donation","Other Revenue","Interest Income","St. Mary's League Income","Donations & Gifts"
        ],
    'AccountCode':[
        "3010","3020","3030","3040","3050","3060","3070","3080","3090","3100","3110","3120","3130","3140","3150","3160","3170","3180","3190","3200","3210","3220","3230","3240","3250"
        ]
    })


def get_member_txns(since_date):
    _member_txns = {}
    for bank_account in bank_accounts.items():
        # Reset page counter for each account (DBS, NETS etc.)
        has_more_pages = True
        page = 0
        
        # Go through pages (100 txns per page)
        while has_more_pages:
            page += 1
            # This endpoint does not return payments applied to invoices, expense claims or transfers between bank accounts.
            url = f'https://api.xero.com/api.xro/2.0/BankTransactions?where=BankAccount.Code=="{bank_account[1]}"&page={page}'
            _header = {'If-Modified-Since': since_date}
            txns = utils.xero_get(url,**_header)
            if len(txns['BankTransactions']) == 0:
                has_more_pages = False
            else:
                print(color(f"Processing {bank_account[0]}. Page {page}",Colors.blue))
                # Keep only "Type":"RECEIVE" & construct a dict via Python List Comprehension
                _receive_txns = [
                    {
                        # Build the output item
                        "ContactID": _txn['Contact']['ContactID'],
                        "ContactName": _txn['Contact']['Name'],                        
                        "BankAccount": _txn['BankAccount']['Name'],
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

# Explode the Line Items col so that there's one ROW per Line Item.
df = pd.DataFrame(list_all_txns)
df = df.explode('Line Items')

# Add the columns from exploded rows
df["LineItem"] = df["Line Items"].apply(lambda x: x.get('Description'))
df["AccountCode"] = df["Line Items"].apply(lambda x: x.get('AccountCode'))
df["LineAmount"] = df["Line Items"].apply(lambda x: x.get('LineAmount'))

# Find a contact
# df.loc[df['ContactName'] == "Vibin Joseph Kuriakose"]

# Lookup and Account code and Add Account Desc
s = lookup.set_index('AccountCode')['label']
df["Account"] = df["AccountCode"].map(s)
 
# Remove unwanted exploded dict col
df = df.drop(columns=["Line Items"])

# Save to CSV
df = df.drop(columns=["BankAccount","Date","Net Amount"])
df.to_csv('member_contributions.csv',index=False)

# Group by Contacts to show all payments from a member
df_grouped = df.groupby(["ContactID","ContactName","AccountCode","Account"]).sum()
print(color(df.head(5),Colors.white))
print(color(df_grouped.head(5),(200,200,200)))
df_grouped.to_csv('member_contributions_grouped.csv',index=True)
#df_grouped.pivot_table(index=["ContactName","Account"]).to_csv('member_contributions_grouped-1.csv',index=True)

# Ref: https://pbpython.com/pandas-pivot-table-explained.html
# Pivot to show all Accounts in cols
# The values column automatically averages the data so should change to sum. 
df_pivoted = df_grouped.pivot_table(index="ContactName", columns="Account",values="LineAmount", aggfunc=np.sum)
df_pivoted.to_csv('member_contributions_pivoted.csv',index=True)

print(background(color(f"Done",(0,0,0)),Colors.green))
