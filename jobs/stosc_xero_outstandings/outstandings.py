"""
🔹Get the total Receiveables by year
🔹Get the total Outstanding by year

as of a certain date
"""

import utils
from colorama import Fore, init
import pandas as pd

init(autoreset=True)
# initialize empty dataframe
df = pd.DataFrame(columns=['Inv', 'Total', 'Due'])
has_more_pages = True
page = 0

# Go through pages (100 txns per page)
while has_more_pages:
    page += 1
    invoices = utils.xero_get(f"https://api.xero.com/api.xro/2.0/Invoices?Statuses=AUTHORISED,PAID&where=Type%3D%22ACCREC%22&summaryOnly=true&page={page}")
    invoice_list = invoices['Invoices']
    if len(invoices['Invoices']) == 0:
        has_more_pages = False
    else:
        print(f"{Fore.YELLOW}Processing page {page}")
        for invoice in invoice_list:
            # print(f"{Fore.BLACK}Processing Invoice {invoice['InvoiceNumber']} for {invoice['Contact']['Name']}")
            if invoice['Overpayments']:
                print(f"{Fore.Red} HANDLE THIS")
            if invoice['Prepayments']:
                print(f"{Fore.Red} HANDLE THIS")
            try:
                type, year, _ = invoice['InvoiceNumber'].split('-')
                year = f"20{year}"
            except ValueError as e:
                if e.args[0] == 'not enough values to unpack (expected 3, got 2)':
                    # Special Handling: a couple of invoices of type INV-0003 were issued in year 2020
                    if invoice['InvoiceNumber']=='INV-0003':
                        year = "2019"
                    elif invoice['InvoiceNumber']=='INV-0007':
                        year = "2019"
                    else:
                        raise e
                else:
                    raise e

            if invoice['InvoiceNumber']=='INV-0003':
                temp_df = pd.DataFrame([{'Inv': 'S-19', 'Total': invoice['Total'], 'Due': invoice['AmountDue']}])
                df = pd.concat([df,temp_df], ignore_index=True)
            elif invoice['InvoiceNumber']=='INV-0007':
                temp_df = pd.DataFrame([{'Inv': 'S-19', 'Total': invoice['Total'], 'Due': invoice['AmountDue']}])
                df = pd.concat([df,temp_df], ignore_index=True)
            elif invoice['InvoiceNumber'].startswith('INV'):
                # Subscriptions
                x = f"S-{invoice['InvoiceNumber'].split('-')[1]}"
                temp_df = pd.DataFrame([{'Inv': x, 'Total': invoice['Total'], 'Due': invoice['AmountDue']}])
                df = pd.concat([df,temp_df], ignore_index=True)
            elif invoice['InvoiceNumber'].startswith('HF-'):
                # Harvest Festival Invoice
                x = f"H-{invoice['InvoiceNumber'].split('-')[1]}"
                temp_df = pd.DataFrame([{'Inv': x, 'Total': invoice['Total'], 'Due': invoice['AmountDue']}])
                df = pd.concat([df,temp_df], ignore_index=True)            
            else:
                raise 

df_grouped = df.groupby('Inv').sum()
# df_grouped['%'] = df_grouped.apply(lambda x: x['Due']/x['Total'] * 100 if x['Total']!=0 else 0, axis=1)
# df_grouped['%'] = df_grouped['%'].round(2)
# df_grouped['%'] = df_grouped['%'].apply(lambda x: '{:.1f}%'.format(x))

# Remove rows that have the "Due" column = 0
df_grouped = df_grouped[df_grouped['Due']!=0]

df_grouped['Total'] = df_grouped['Total'].apply(lambda x: '$ {:,.0f}'.format(x))
df_grouped['Due'] = df_grouped['Due'].apply(lambda x: '$ {:,.0f}'.format(x))

# Reset the index
df_reset = df_grouped.reset_index()
# Extract the year from the index column
df_reset['year'] = df_reset.iloc[:, 0].str.extract('(\d+)').astype(int)
# Sort the dataframe based on the extracted year
df_sorted = df_reset.sort_values(by='year')
# Set the index back to the original column and drop the year column
df_sorted = df_sorted.set_index(df_sorted.columns[0]).drop('year', axis=1)

print(f"\n{Fore.WHITE}{df_sorted.to_string()}\n")

import pickle
filehandler = open(b"outstandings.pickle","wb")
pickle.dump(df_sorted,filehandler)
filehandler.close()
print("Done")
