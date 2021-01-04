# xero_helpers
Helper Scripts for Xero. Since one can to bulk-update Xero invoices, use these helper script to do that. This script is not generic and is created for my specific needs:

* Move a lot of AUTHORIZED invoices to DRAFT mode keeping the same Invoice numbers

This is done by first renaming the original invoice (as we want to re-use the same invoice numbers), VOIDing them and then recreating them.

![image](https://user-images.githubusercontent.com/327990/103514620-f7460c00-4ea7-11eb-9a6b-f797fd85bdf5.png)


## 

Create a my_secrets.py file in the root that contains your [Xero tenant ID and clientID](https://developer.xero.com/documentation/oauth2/sign-in):

```
xero_DEMO_tenant_ID = 'XXXX-XXXX-XXXX-XXXX-XXXX'
xero_client_id = "XXXXX"
```

You should also have a file named `xero_refresh_token.txt` that contains your refresh token to call the Xero APIs

All Contacts whose Authorzied invoices I wish to change are in a `contacts.txt` file. Change this to suit your needs.

## Setup Python Environment

Setup your virtual environment. 
```bash
python -m venv .env
```

Activate (on Windows):
```dos
.env\Scripts\activate.bat
```

On linux: 
```bash
source .env/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Upgrade dependencies

```bash
pip install --upgrade -r requirements.txt
```
