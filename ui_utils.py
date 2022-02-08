import platform
from colorama import init, Fore, Back, Style, deinit


"""
Utils class for authly with introduction messages, table/other prints, platform information and other utility functions used in authly
"""

def remove(string):
    # Remove extra spaces in input
    return string.replace(" ", "")

def get_platform():
    # Get platform information
    return platform.system()

def norm_print_t(str1,str2):
    """
    Print normal string with 2 arg
    """
    print(Fore.YELLOW+ '[-]'+ Fore.WHITE+ str1 +'-->'+ str2+ Fore.RESET)\

def yell_print(str):
    # Print normal string in Yellow color
    print(Fore.YELLOW+ '[?]'+ Fore.YELLOW+ str + Fore.RESET)

def norm_print(str):
    """
    Print normal string
    """
    print(Fore.YELLOW + '[-] ' + Fore.CYAN + str + Fore.RESET)

def success_print(str):
    """
    Print success string
    """
    print(Fore.YELLOW + '[-] ' + Fore.GREEN + str + Fore.RESET)

def space_print():
    """
    Print white lines
    """
    print(Fore.YELLOW + "[ ]" + Fore.RESET)

def hash_print():
    """
    Print series of hashes
    """
    print(Fore.YELLOW + "[#] " + Fore.GREEN +
          "######################################################" +
          Fore.RESET)

def dash_print():
    """
    Print series of dashes
    """
    print(Fore.YELLOW + "[-] " + Fore.GREEN +
          "------------------------------------------------------" +
          Fore.RESET)


def imp_print(str):
    """
    Print important messages
    """
    print(Fore.LIGHTRED_EX + "[!] " + str + Fore.RESET)


def print_intro():
    """
    Print program introduction
    """

    hash_print()
    norm_print("St. Thomas Orthodox Syriaan Cathedral, Singapore ⛪")
    norm_print("Version - " + Fore.YELLOW + " 1.0.0")
    norm_print("Last Modified On - " + Fore.CYAN + " Feb 08, 2022")
    norm_print("Author - " + Fore.CYAN + "accounts@stosc.com")
    hash_print()
    print()

def isint(str):
    """
    Check if given string is valid integer. Used for validations and ruse for exiting program early
    """
    try:
        int(str)
        return True
    except:
        return False