
import requests
import utils
# https://github.com/CodeForeverAndEver/ColorIt
from colorit import *

# Use this to ensure that ColorIt will be usable by certain command line interfaces
init_colorit()

def filter_journal(_journals):
    for _journal in _journals['Journals']:
        print(f"\nSource Type: {_journal['SourceType']}")
        for journal_line in _journal['JournalLines']:
            print(f"Account Type: {journal_line['AccountType']} towards {journal_line['AccountName']} ({journal_line['AccountCode']}) the amount {journal_line['NetAmount']}")            
    return _journals

def save_journals(_journals):    
    print("Saved")    

url = f"https://api.xero.com/api.xro/2.0/Journals"
# Get Invoices Created only this year 
_header = {'If-Modified-Since': utils.year_start()}
journals = utils.xero_get(url,**_header)

filtered_journals = filter_journal(journals)

save_journals(filtered_journals)

print("DONE")
