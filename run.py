from pyfiglet import figlet_format
from colorit import *
from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem

from payments_oustanding import generate_payments_oustanding
from generate_Xero_Contact_List import Xero_Contact_List
from GB_list import generate_GB_List
init_colorit()


def log(string, font_color, figlet=False):
    if figlet:
        print(color(figlet_format(string, font="slant"), font_color))
    else:
        print(color(string, font_color))


def main():
    """
    Simple CLI for sending emails using SendGrid
    """
    log("STOSC Tools", Colors.orange, figlet=True)
    log("Welcome to STOSC Tools CLI", Colors.green)
    log("St.Thomas Orthodox Syrian Cathedral, Singapore", Colors.green)

    menu = ConsoleMenu(
        title="STOSC Tools",
        subtitle="For Xero and CRM Functions",
        prologue_text="Select an option:",
    )

    menu_generate_payments_oustanding = FunctionItem("Generate Payments Outstanding", generate_payments_oustanding)
    menu_Xero_Contact_List = FunctionItem("Generate Xero Contact List", Xero_Contact_List)
    menu_generate_GB_List = FunctionItem("Generate GB List", generate_GB_List)
    menu_member_contrib = FunctionItem("TBD: Member Contribution Matrix", generate_GB_List)
    
   

    menu.show()


if __name__ == "__main__":
    main()
