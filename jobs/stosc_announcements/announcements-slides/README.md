## Setup
- Create a virtual environment (Python 3.9+) and install packages,
```{console}
python3 -m venv env
source env/bin/activate  (linux)  | & ./env/Scripts/Activate.ps1 (Windows)
pip install --upgrade pip (Linux) | python3 -m pip install --upgrade pip (windows)
pip install -r requirements.txt
```
- if using spacy, download the english language model
```{console}
python -m spacy download en_core_web_sm
```
- download the `google_service_account.json` and save in root folder
### how to generate
``Go to the Google Cloud Console and select your project.
Click on the Navigation menu icon in the top left corner and select APIs & Services > Credentials.
Click on the Create credentials button and choose Service account.
Fill in the service account details, such as name, description, and role. You can also grant access to other users or groups if needed.
Click on the Create and continue button.
On the next page, click on the Create key button and choose JSON as the key type.
Click on the Create button. A JSON file will be downloaded to your computer. This file contains your service account key information, such as client ID, private key, and email address.
Save the JSON file in a secure location. You will need it to set the GOOGLE_APPLICATION_CREDENTIALS environment variable.``

- Save the `.env` file in the root
- Create an `output` folder in the root