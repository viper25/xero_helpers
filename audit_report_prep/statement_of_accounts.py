"""
Download member contributions from DynamoDB, and pivot to create the Statement of Accounts for
preparing Audit report. Note this has only active members, so if there are any that have left mid-year
manually adjust those lookups.

ENSURE THAT DDB table stosc_xero_member_payments is updated and latest!

Make sure xero_contacts.csv is updated first.
TODO: Generate this on the fly from Xero API. Also First Evangelic church is  

"""
import boto3
import pandas as pd

import my_secrets

TABLE_NAME_MEMBER_PAYMENTS = "stosc_xero_member_payments"
YEAR_TO_GENERATE_REPORT_FOR = '2022'


def get_df_from_ddb(table_name):
    session = boto3.Session(
        aws_access_key_id=my_secrets.DDB_ACCESS_KEY_ID,
        aws_secret_access_key=my_secrets.DDB_SECRET_ACCESS_KEY,
        region_name="ap-southeast-1"
    )

    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    _df = pd.DataFrame(data)

    # Filter for current year
    # create a filter
    year_mask = _df['AccountCode'].str.startswith(YEAR_TO_GENERATE_REPORT_FOR)
    filtered_df = _df[year_mask]

    pivot_df = filtered_df.pivot_table(index=['ContactName', 'ContactID'], columns='Account',
                                       values='LineAmount').reset_index()

    pivot_df.columns.name = None  # removing the name of columns level
    pivot_df = pivot_df.fillna(0)  # replacing NaN with 0 (if any)

    return pivot_df


def lookup_member_code_from_contact_id(_df):
    # Get lookup_df from csv file which is one folder level up
    lookup_df = pd.read_csv('../csv/xero_contacts.csv')
    # Remove the 'Name' column from the lookup DataFrame
    lookup_df.drop(columns='Name', inplace=True)
    merged_df = pd.merge(_df, lookup_df, on='ContactID', how='left')

    # After the merge, your DataFrame will have an extra column named `memberCode`.
    # Now, replace 'ContactID' with 'memberCode'
    merged_df.drop(columns='ContactID', inplace=True)  # drop the original ContactID column

    # Replace NaN with 'NA' in the memberCode column (members such as DBS, STOSC etc.)
    merged_df['memberCode'].fillna('NA', inplace=True)

    # Create Name column from ContactName and memberCode
    merged_df['Name'] = merged_df['ContactName'] + ' (' + merged_df['memberCode'] + ')'
    merged_df = merged_df.drop(['ContactName', 'memberCode'], axis=1)

    # Move the Name column to the 1st column
    cols = list(merged_df.columns.values)
    cols.remove('Name')  # Remove 'Name' from the list
    merged_df = merged_df[['Name'] + cols]  # Insert them at the start

    return merged_df


# Main program
if __name__ == '__main__':

    # Inform user to ensure that xero_contacts.csv is updated first
    print("Is xero_contacts.csv updated? If not, please update it first")
    input("Press Enter to continue...")

    print("Is DDB table stosc_xero_member_payments updated? If not, please update it first")
    input("Press Enter to continue...")

    filename = f"{TABLE_NAME_MEMBER_PAYMENTS}_{YEAR_TO_GENERATE_REPORT_FOR}.csv"

    df = get_df_from_ddb(table_name=TABLE_NAME_MEMBER_PAYMENTS)
    df = lookup_member_code_from_contact_id(df)

    df.to_csv(filename, index=False)
    print(f"Downloaded {len(df)} rows to {filename} for {YEAR_TO_GENERATE_REPORT_FOR}")
