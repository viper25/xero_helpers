# pip install tk
import tkinter as tk
from tkinter import filedialog
import generate_Xero_Contact_List

PADDING = 5


def contact_List():
    generate_Xero_Contact_List.Xero_Contact_List()


def execute_program2():
    pass


def execute_program3():
    pass


window = tk.Tk()
window.title("STOSC Utilities")
# Set the window size
width = 600
height = 400

# Fix the window size by setting minsize and maxsize to the same dimensions
window.minsize(width, height)
window.maxsize(width, height)

# Center the window on the screen
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x_cordinate = int((screen_width / 2) - (width / 2))
y_cordinate = int((screen_height / 2) - (height / 2))
window.geometry("{}x{}+{}+{}".format(width, height, x_cordinate, y_cordinate))


def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_path_label.config(text=folder_path)
    else:
        folder_path_label.config(text="No folder selected")


# Create buttons
button1 = tk.Button(window, text="Generate Contact List", command=contact_List)
button2 = tk.Button(window, text="Execute Program 2", command=execute_program2)
button3 = tk.Button(window, text="Execute Program 3", command=execute_program3)

lbl_header = tk.Label(text="Hello, STOSC, click any of the buttons below to execute a program.")
select_button = tk.Button(window, text="Select Folder", command=select_folder)
folder_path_label = tk.Label(window, text="No folder selected", wraplength=200)

# Grid layout
lbl_header.grid(row=0, column=0, pady=10, padx=PADDING)
button1.grid(row=1, column=0, pady=10, padx=PADDING)
select_button.grid(row=1, column=1, pady=10, padx=PADDING)
folder_path_label.grid(row=1, column=2, padx=PADDING)
button2.grid(row=2, column=0, pady=10, padx=PADDING)
button3.grid(row=3, column=0, pady=10, padx=PADDING)

# Start the tkinter main loop
window.mainloop()
