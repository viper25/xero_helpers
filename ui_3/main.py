import subprocess
from InquirerPy import prompt, inquirer

questions = [
    {
        "type": "input",
        "message": "What's your name:",
        "name": "name",
        "transformer": lambda result: f"Hello {result}",
    },
    {
        "type": "checkbox",
        "name": "languages",
        "message": "What languages do you know:",
        "choices": ["Python", "JavaScript", "Rust", "Go"],
    },
    {
        "type": "list",
        "message": "What do you want to run:",
        "choices": ["Create Invoices", "Create Contacts", "Create Items", "Create Payments"],
    },
    {
        "type": "list",
        "message": "What's your favourite programming language:",
        "choices": ["Go", "Python", "Rust", "JavaScript"],
    },
    {"type": "confirm", "message": "Confirm?"},
]


script_choices = ["script1.py", "script2.py"]
selected_script = inquirer.select(message="Select a script to run:", choices=script_choices).execute()

# Run the selected script with the temporary config file
subprocess.run(["python", selected_script])

result = prompt(questions)
name = result["name"]
program = result[1]
fav_lang = result[2]
confirm = result[3]
