'''
Get the TenantID and Tokens the FIRST tiem one uses Xero
Refer to https://developer.xero.com/documentation/guides/oauth2/pkce-flow
An easy alternative is https://github.com/XeroAPI/xoauth/releases/download/v1.1.0/xoauth_1.1.0_windows_amd64.tar.gz
'''
import requests
import json
import sys
import base64
import hmac
import hashlib


CLIENT_ID = "xxx"
REDIRECT_URI = "https://stosc.com/xero"


def generate_code_challenge():
    #code_verifier = os.urandom(32)
    code_verifier = bytes('xCfhablYhXr.3OXNzCTNlxwEdtO1WqmnV99B2Hh.SOGivBfGt.5bAZz.SAG1lUqPKl8WDwqR-eduDPiYyJtd8ZLeqB8bb57N_YvwHL8MFR5PFdg~wk7pcytX~YCeOos0', 'utf-8')
    
    code_challenge = base64.urlsafe_b64encode(
        hmac.new(code_verifier,
                 msg=code_verifier,
                 digestmod=hashlib.sha256).digest()).decode()
    # return code_challenge, code_verifier
    # https://tonyxu-io.github.io/pkce-generator/
    return '0hzImwoP9_jBbt3bRnxtLHuyEJBk0O91CxMO-K_lnEo', 'xCfhablYhXr.3OXNzCTNlxwEdtO1WqmnV99B2Hh.SOGivBfGt.5bAZz.SAG1lUqPKl8WDwqR-eduDPiYyJtd8ZLeqB8bb57N_YvwHL8MFR5PFdg~wk7pcytX~YCeOos0'
   
def exchange_code(code_verifier,code):
    url = 'https://identity.xero.com/connect/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'code_verifier': code_verifier,
        'redirect_uri': REDIRECT_URI,
        'code': code,
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code'
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response

def check_tenants(access_token):
    url = 'https://api.xero.com/connections'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    return response

code_challenge, code_verifier = generate_code_challenge()
# paste this URL in the browser
url = f"https://login.xero.com/identity/connect/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri=https%3A%2F%2Fstosc.com%2Fxero&scope=openid profile email accounting.transactions&state=123123&code_challenge={code_challenge}&code_challenge_method=S256"

# Grab the "code" parameter and paste here
verification_code_returned="xxx"
code_verifier= 'xCfhablYhXr.xxx.SOGivBfGt.5bAZz.SAG1lUqPKl8WDwqR-eduDPiYyJtd8ZLeqB8bb57N_YvwHL8MFR5PFdg~wk7pcytX~YCeOos0'

# Exchange the code
token_response = exchange_code(code_verifier,verification_code_returned)
# if token_response.status_code != 200:
#     print("Error: " + str(token_response.status_code))
#     print(token_response.text)
#     sys.exit(0)

print("OK")

access_token = "xxx.eyJuYmYiOjE2MzU4NDMzODcsImV4cCI6MTYzNTg0NTE4NywiaXNzIjoiaHR0cHM6Ly9pZGVudGl0eS54ZXJvLmNvbSIsImF1ZCI6Imh0dHBzOi8vaWRlbnRpdHkueGVyby5jb20vcmVzb3VyY2VzIiwiY2xpZW50X2lkIjoiQUUzNzE2QkJDQkI2NDZCQ0I2OUYxQTNGNDVEMzE4NUIiLCJzdWIiOiIzMDZiMmI0N2U1Y2Q1YjczODZhNWVlOGU5NzBiNDY0MiIsImF1dGhfdGltZSI6MTYzNTg0MjQxMiwieGVyb191c2VyaWQiOiJiYjI2NDVhNi0wZTBmLTQxZDMtOWE5MS01Njc5ODI3ZDExMmUiLCJnbG9iYWxfc2Vzc2lvbl9pZCI6ImE2YjU4YWIxNjc5YzRiYWFhMTBkMDJjMzVhYjQ5ODllIiwianRpIjoiZmI4OTQxODYyNGM4MzhhZWQ0YWRhMzY3YzYxOWU4OTkiLCJhdXRoZW50aWNhdGlvbl9ldmVudF9pZCI6ImI0YzZkZGQ3LTNiNGEtNDgwYi04OTBkLWUxZGIxZTQ2MWUxMSIsInNjb3BlIjpbImVtYWlsIiwicHJvZmlsZSIsIm9wZW5pZCIsImFjY291bnRpbmcucmVwb3J0cy5yZWFkIiwiYWNjb3VudGluZy5zZXR0aW5ncy5yZWFkIiwiYWNjb3VudGluZy50cmFuc2FjdGlvbnMiLCJhY2NvdW50aW5nLmpvdXJuYWxzLnJlYWQiLCJhY2NvdW50aW5nLnRyYW5zYWN0aW9ucy5yZWFkIiwiYWNjb3VudGluZy5jb250YWN0cy5yZWFkIiwib2ZmbGluZV9hY2Nlc3MiXX0.j_YA66AkVJE5mnRdGGY9jTRoOz63TZxn2YrJDfFhB4L33skuQKRH_IMDsqa2WLkef-ZtR41zEVMonlDPJgcr_TbiFbzaRfR5kwc4MbxGmh54QnbtMnSSWSMrfCNwR8rhkfR2IAf6HJM-ePXLjO2TxSMxyqxgV3vJu4d9kFgMdNtmmkBN_nBBhGRdTA8hVeaxMDlo-BO096LlWpLO-W45KK_UrVKMHY2zzNAYfBtSR-9iEMtF4vaFPK-F20E2JMk3oe9p_PGP2dcaLQKXNISiq9nUZfh9G4nFlmwAr87b1mgh6V1BgyL3itr6j6fLO7hCU21Q0a9xNYQEoikscj25Cw"

# Check the tenants you’re authorized to access
response = check_tenants(access_token)
for tenant in response.json():
    print(f"Tenant Name: {tenant['tenantName']}")
    print(f"Tenant ID: {tenant['tenantId']}")

print("OK")