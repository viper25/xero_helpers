import os
import pygsheets
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import models.models as models  

load_dotenv()

SERVICE_ACCOUNT_FILE = "google_service_account.json"
SPREADSHEET_ID = os.environ.get("data_spreadsheet_id")
gc = pygsheets.authorize(service_file=SERVICE_ACCOUNT_FILE)
sh = gc.open_by_key(SPREADSHEET_ID)


def get_sheet_data(sheet_name):
    try:
        wks = sh.worksheet_by_title(sheet_name)
        df = wks.get_as_df()
        return df
    except Exception as e:
        raise Exception(f"Error in getting sheet data: {e}")


def add_sheet_data(sheet_name, values):
    try:
        wks = sh.worksheet_by_title(sheet_name)
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in values:
            row.append(current_datetime)
        wks.append_table(
            values, start="A1", end=None, dimension="ROWS", overwrite=False
        )
    except Exception as e:
        raise Exception(f"Error in updating sheet data: {e}")


def birthdays():
    sheet_name = "birthdays"
    try:
        df = get_sheet_data(sheet_name)
        birthdays = df["name"].tolist() 
        return birthdays
    except Exception as e:
        raise Exception(f"Error in getting birthdays: {e}")

def get_announcements()->list[models.Announcement]:
    sheet_name = "announcements"
    try:
        df = get_sheet_data(sheet_name)
        df["announcement_date"] = pd.to_datetime(df["announcement_date"]).dt.date
        df = df[df["announcement_date"] >= datetime.now().date()]
        announcements = []
        # Columns: announcement_date	Type	Title	AnnouncementText	image_url
        for index, row in df.iterrows():
            try:
                announcement_type = models.Layouts(row["Type"])
            except Exception as e:
                announcement_type = models.Layouts.Text
            
            announcements.append(models.Announcement(announcement_type, row["Title"], row["AnnouncementText"], row["image_url"]))
        return announcements
    except Exception as e:
        raise Exception(f"Error in getting announcements: {e}")

def get_obituaries()->list[models.Obituaries]:
    sheet_name = "obituaries"    
    try:        
        df = get_sheet_data(sheet_name)
        df["announcement_date"] = pd.to_datetime(df["announcement_date"]).dt.date
        df = df[df["announcement_date"] >= datetime.now().date()]
        obituary_data = []
        for index, row in df.iterrows():
            obituary_data.append(models.Obituaries(row["obituary_data"], row["image_url"]))
            # obituary_data.append({"text": row["obituary_data"], "image_url": row["image_url"]})
        return obituary_data
    except Exception as e:
        raise Exception(f"Error in getting obituaries: {e}")

# sheet name manual_trigger, Fields trigger_by	completed_date.
# only get the last record and return if completed_date is empty 
def get_manual_triggers()->str:
    sheet_name = "manual_trigger"
    try:
        df = get_sheet_data(sheet_name)
        # get the last record
        df = df.tail(1)
        # check if completed_date field is not empty
        if not df["completed_date"].isnull().values.any():
            # return trigger_by
            return df["trigger_by"].values[0]
        else:        
            return ""
    except Exception as e:
        raise Exception(f"Error in getting manual triggers: {e}")
    
def update_manual_trigger():
    sheet_name = "manual_trigger"
    # add a new row with trigger_by and completed_date
    values = [["manual", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
    try:
        add_sheet_data(sheet_name, values)
    except Exception as e:
        raise Exception(f"Error in updating manual triggers: {e}")
        

#######################################################################################################
# Google drive functions
# check if folder exist on Google Drive
def drive_check_folder_exists(drive_service, folder_name, parent_folder_id):
    response = drive_service.files().list(
        q=f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)").execute()
    if response.get("files"):
        return response["files"][0]["id"]
    else:
        return None
# create a google drive folder
def drive_create_folder(drive_service, folder_name, parent_folder_id):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    response = drive_service.files().create(body=file_metadata, fields='id').execute()
    return response.get('id')
   
# copy file to another folder
def drive_copy_file(drive_service, file_id, folder_id, new_file_name=""):
    file_metadata = {
        'parents': [folder_id]
    }
    if new_file_name:
        file_metadata["name"] = new_file_name
    response = drive_service.files().copy(fileId=file_id, body=file_metadata).execute()
    return response.get('id')