#!/usr/bin/python
import sys
from ui_utils import *
from tabulate import tabulate

from generate_Xero_Contact_List import Xero_Contact_List


space_print()
space_print()
print_intro()

# norm_print("Normal Print")
# success_print("OK")
# imp_print('Execution Failed!')


table=[[0,"Generate Member Listing"],[1,"Generate Member Payments"],[2,"Generate Subscription Invoices"],[3,"Connect to RDS"]]
headers=["Index","Option"]
print(tabulate(table,headers,tablefmt="grid"))
inp_index = input('[?] Index Number: ')

if inp_index == "0":
    Xero_Contact_List()
elif inp_index == "1":
    print("Generate Member Payments")

print(f"Selection: {inp_index}")