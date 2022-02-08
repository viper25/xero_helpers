#!/usr/bin/python
from ui_utils import *
from tabulate import tabulate

from generate_Xero_Contact_List import Xero_Contact_List

space_print()
print_intro()

# norm_print("Normal Print")
# success_print("OK")
# imp_print('Execution Failed!')


table = [
    [1, "Generate Member Listing (csv)"],
    [2, "Update & Generate General Body Listing (csv)"],
    [3, "Generate Member Contribution Matrix (csv)"],
    [4, "Update Member Contribution DDB Tables"],
    [5, "Create Subscription Invoices (Xero)"],
    [6, "Create Harvest Festival Invoices (Xero)"],
]
headers = ["Index", "Option"]
print(tabulate(table, headers, tablefmt="orgtbl"))
inp_index = input("\n[?] Index Number: ")

if inp_index == "1":
    norm_print("This will generate an excel of members with their member codes and Xero ContactIDs for use in the Xero API")
    # Xero_Contact_List()
elif inp_index == "2":
    norm_print("Generate GB Listing in excel as well as update the CRM DB with the GB eligibility status")


print(f"\nSelection: {inp_index}")
