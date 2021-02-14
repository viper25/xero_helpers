# xero_helpers
Helper Scripts for Xero. Since one can to bulk-update Xero invoices, use these helper script to do that. This script is not generic and is created for my specific needs:

## Update Xero Invoice status 
Move a lot of AUTHORIZED invoices to DRAFT mode keeping the same Invoice numbers. File is `xero_invoice.py`

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

## Invoices outstanding
We keep all Xero invoices in "Draft" mode so as not to show them as Receiables in P&L and inflate revenue. But we need to know among these drafts, for all members, how many are oustanding on payments (as if the Invoices were in "Approved Mode"). This is needed to find eleigible members for GB. File is `payments_oustanding.py`

A CSV is generated. Users who have a payment delta of > 50% (or 0.5) are not eligible.

![image](https://user-images.githubusercontent.com/327990/107588103-fee29880-6c3d-11eb-994e-5edce62d68ed.png)


### Setup Python Environment

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
