from dotenv import load_dotenv
load_dotenv()

import os, sys, time
from datetime import datetime
import requests as http_requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from helpers.db_helper import get_birthdays, get_anniversaries
from helpers.gs_data_helper import drive_check_folder_exists, drive_copy_file, drive_create_folder, get_announcements, get_manual_triggers, get_obituaries, update_manual_trigger
from helpers.text_split_helper import split_text_into_slides,get_effective_lines,layout_config
import models.models as models


NO_OF_BIRTHDAYS_TO_SHOW = 10
NO_OF_ANNIVERSARIES_TO_SHOW = 7
# Copy the template presentation
template_ppt_id = os.getenv("template_ppt_id")
output_folder_id = os.getenv("output_folder_id")

# Initialize Google Slides API
scopes = ["https://www.googleapis.com/auth/presentations", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file("google_service_account.json", scopes=scopes)
slides_service = None
drive_service = None
current_time = None
sub_folder_id = None

# Function to print editable placeholders in each layout
def print_editable_placeholders(layouts):
    for layout in layouts:
        layout_name = layout.get('layoutProperties', {}).get('displayName', 'N/A')
        print(f"Layout: {layout_name} id: {layout['objectId']}")

        for element in layout.get('pageElements', []):
            element_type = element.get('shape', {}).get('shapeType', '')

            element_id = element.get('objectId', 'N/A')
            print(f"  Editable Placeholder: {element_id}, Type: {element_type}")

def get_layout_id_by_name(layout_name, layouts):
    for layout in layouts:
        if layout.get('layoutProperties', {}).get('displayName', "N/A") == layout_name:
            return layout['objectId']
    return None

def get_max_names(length: int, layout: str):
    max_names: int = NO_OF_BIRTHDAYS_TO_SHOW if layout == "Birthday" else NO_OF_ANNIVERSARIES_TO_SHOW
    variant: int = 2 if layout == "Birthday" else 1
    if length <= max_names + variant:
        max_names = max_names + variant
    if length % max_names == 1:
        max_names = max_names + 1
    return max_names


# create Request Object
def create_request_object(layouts, layout, names_list: list[str], date_range_text="",title=""):
    # sleep for 1 sec
    time.sleep(0.1)
    time_string = datetime.now().strftime("%H%M%S%f")
    layout_id = get_layout_id_by_name(layout, layouts)
    names_list_l = ""
    names_list_r = ""    
    bullet = "🎂 " if layout.lower() == "birthday" else "🎉 " if layout.lower() == "anniversary" else ""

    if layout.lower() == "birthday":
        # split the names into two sets. if more than 10 divide by 2 (and if odd put more in first), else first set have 5 and second set have remaining        
        if len(names_list) > 10:
            # if odd divide by 2 and use next integer, else divide by 2
            count_1 = len(names_list) // 2 if len(names_list) % 2 == 0 else len(names_list) // 2 + 1
            names_list_l = names_list[:count_1]
            names_list_r = names_list[count_1:]
        else:
            names_list_l = names_list[:5]
            names_list_r = names_list[5:]
    else:        
        names_list_l = names_list

    requests = [
        {
            "createSlide": {
                "objectId": f"{time_string}_{layout}",
                "slideLayoutReference": {
                    "layoutId": layout_id
                },
                "placeholderIdMappings": []
            }
        },
    ]
    if layout.lower() == "image":
        return requests
    
    if names_list_l:
        # add a bullet character to each name
        names_list_left = "\n".join([f"{bullet}{name}" for name in names_list_l])
        placeholder_mapping_1 = {
            "layoutPlaceholder": {
                "type": "BODY",
                "index": 0
            },
            "objectId": f"{layout_id}_main_L_{time_string}"
        }
        insert_text_1 = {
            "insertText": {
                "objectId": f"{layout_id}_main_L_{time_string}",
                "text": names_list_left,
            }
        }
        requests[0]["createSlide"]["placeholderIdMappings"].append(placeholder_mapping_1)
        requests.append(insert_text_1)
    if names_list_r:
        names_list_right = "\n".join([f"{bullet}{name}" for name in names_list_r])

        placeholder_mapping_2 = {
            "layoutPlaceholder": {
                "type": "BODY",
                "index": 1
            },
            "objectId": f"{layout_id}_main_R_{time_string}"
        }
        insert_text_2 = {
            "insertText": {
                "objectId": f"{layout_id}_main_R_{time_string}",
                "text": names_list_right,
            }
        }
        requests[0]["createSlide"]["placeholderIdMappings"].append(placeholder_mapping_2)
        requests.append(insert_text_2)
    if date_range_text:
        placeholder_mapping_3 = {
            "layoutPlaceholder": {
                "type": "TITLE",
                "index": 0
            },
            "objectId": f"{layout_id}_date_{time_string}"
        }
        insert_text_3 = {
            "insertText": {
                "objectId": f"{layout_id}_date_{time_string}",
                "text": date_range_text,
            }
        }
        requests[0]["createSlide"]["placeholderIdMappings"].append(placeholder_mapping_3)
        requests.append(insert_text_3)
    if title:
        placeholder_mapping_4 = {
            "layoutPlaceholder": {
                "type": "TITLE",
                "index": 0
            },
            "objectId": f"{layout_id}_title_{time_string}"
        }
        insert_text_4 = {
            "insertText": {
                "objectId": f"{layout_id}_title_{time_string}",
                "text": title,
            }
        }
        requests[0]["createSlide"]["placeholderIdMappings"].append(placeholder_mapping_4)
        requests.append(insert_text_4)
    # print(layout, requests)
    return requests

# Create and populate a new slide
def create_and_populate_slides(presentation_id, layout: str, names_obj:models.NamesList):    
    names = names_obj.data 
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()        
    layouts = presentation.get('layouts', [])    
    max_names: int = get_max_names(len(names), layout)
    for i in range(0, len(names), max_names):
        requests = create_request_object(layouts,layout, names[i:i + max_names], names_obj.date_range)
        # execute the request
        slides_service.presentations().batchUpdate(presentationId=presentation_id,
                                                   body={"requests": requests}).execute()
# presentation_id, page_id, image_url,type):
def place_image_on_a_slide(presentation_id, page_id, image_url, type):
    # Get actual URL after redirection
    image_url = http_requests.get(image_url).url
    requests = []
    # Configuration for different image types
    image_configs = {
        "obituary": {"width": 173, "height": 196, "translateX": 62, "translateY": 43},
        "image": {"width": 960, "height": 540, "translateX": 0, "translateY": 0},
        "textandimage": {"width": 450, "height": 460, "translateX": 525, "translateY": 80}
    }

    config = image_configs.get(type.lower())

    if config:
        request = {
            "createImage": {
                "url": image_url,
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {
                        "width": {"magnitude": config["width"], "unit": "PT"},
                        "height": {"magnitude": config["height"], "unit": "PT"}
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": config["translateX"],
                        "translateY": config["translateY"],
                        "unit": "PT"
                    }
                }
            }
        }

        requests.append(request)
        # Execute the request
        body = {'requests': requests}
        response = slides_service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
        return response

    else:
        raise ValueError(f"Unknown image type: {type}")
    

# def create_and_populate_slides_obituary(presentation_id, data: list[str]):
#     presentation = slides_service.presentations().get(presentationId=presentation_id).execute()        
#     layouts = presentation.get('layouts', [])  
#     for i in range(0, len(data), 1):
#         text = data[i].text.upper()
#         image_url = data[i].image_url
#         requests = create_request_object(layouts, "Obituary", [text])
#         # requests = create_request_object_obituary(text) 
#         # execute the request
#         response = slides_service.presentations().batchUpdate(presentationId=presentation_id,
#                                                               body={"requests": requests}).execute()
#         new_slide_id = response["replies"][0]["createSlide"]["objectId"]
#         # Fill the image placeholder with an image        
#         if image_url:
#             try:
#                 response = place_image_on_a_slide(presentation_id=presentation_id, page_id=new_slide_id, image_url=image_url)
#             except Exception as e:
#                 print(e)
#                 pass

def create_and_populate_slides_announcements(presentation_id, data: list[models.Announcement]):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    layouts = presentation.get('layouts', [])
    for i in range(0, len(data), 1):
        try:
            type = data[i].announcement_type
            # get text of announcement_type
            type_str = models.Layouts(type).name
            # if title == "" or "NA" or "N/A" the set title to None
            title = data[i].title if data[i].title and data[i].title.lower() not in ["na", "n/a"] else None
            if type_str.lower() not in ["text", "textandimage"]:
                title = None
            text = data[i].text
            if type_str.lower() == "obituary":
                text = text.upper()
            image_url = data[i].image_url
            requests = create_request_object(layouts, type_str, [text],title=title)
            # execute the request
            response = slides_service.presentations().batchUpdate(presentationId=presentation_id,
                                                                body={"requests": requests}).execute()
            new_slide_id = response["replies"][0]["createSlide"]["objectId"]
            # Fill the image placeholder with an image        
            if image_url and type_str.lower() in ["image", "textandimage", "obituary"]:
                try:
                    response = place_image_on_a_slide(presentation_id=presentation_id, page_id=new_slide_id, image_url=image_url, type=type_str)
                except Exception as e:
                    print(e)
                    pass
        except Exception as e:
            print(e)
            pass
            

def export_pdf(presentation_id, pdf_name:str="output.pdf"):
    if not presentation_id:
        print("No presentation id found. Exiting...")
        return
    # Export the presentation as a PDF    
    pdf_data = drive_service.files().export(fileId=presentation_id, mimeType="application/pdf").execute()
    # Create a MediaInMemoryUpload object from the byte stream
    media = MediaInMemoryUpload(pdf_data, mimetype='application/pdf', resumable=True)

    # Upload the PDF to the specified Google Drive folder
    file_metadata = {
        'name': pdf_name,
        'parents': [sub_folder_id]
    }
    request = drive_service.files().create(
        body=file_metadata,
        media_body=media
    )
    request.execute()
    print(f"PDF created: {pdf_name}")
    # Download the presentation as PDF
    # with open(f"output/announcements_{current_time}.pdf", "wb") as f:
    #     f.write(pdf_data)

def export_slide_images(presentation_id):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation.get('slides')
    for slide in slides:
        try:
            slide_id = slide['objectId']
            slide_image = slides_service.presentations().pages().getThumbnail(presentationId=presentation_id,
                                                                              pageObjectId=slide_id).execute()
            image_url = slide_image['contentUrl']
            response = http_requests.get(image_url)
            image_name = f"{slide_id}.png"
            # with open(image_name, "wb") as f:
            #     f.write(response.content)

            # now upload the file to google drive output_folder_id
            file_metadata = {
                'name': image_name,
                'parents': [sub_folder_id]
            }
            media = MediaInMemoryUpload(response.content, mimetype='image/png', resumable=True)
            request = drive_service.files().create(
                body=file_metadata,
                media_body=media
            )
            request.execute()
        except Exception as e:
            print(e)
            pass
    print("Slide images created")

def  generate_birthdays_anniversaries_slides(template_ppt_id,sub_folder_id,export_images=False):
    global slides_service, drive_service, current_time
    # Get birthdays and anniversaries from DB    
    birthdays, anniversaries = None, None
    try:
        birthdays=get_birthdays()
    except Exception as e:
        pass
    try:
        anniversaries = get_anniversaries()
    except Exception as e:
        pass
    
    if not birthdays and not anniversaries:
        print("No birthdays or anniversaries found. Exiting...")
        return
    
    # Print editable placeholders
    # presentation_id = '1d10V90kXAiqPY2k67uyxqLZl4b3hrbUmAjyd0Eqkc0k'    
    # copy from template to the new folder
    try:
        presentation_id = drive_copy_file(drive_service, template_ppt_id, sub_folder_id, f"birthday_anniversary_{current_time}")       
    except Exception as e:
        print(f"Error copying template file: {e}")
        return
    # layouts = presentation.get('layouts', [])

    # print_editable_placeholders(layouts)    
    # Populate slides
    try:
        if birthdays:
            create_and_populate_slides(presentation_id=presentation_id, layout="Birthday", names_obj=birthdays)
            print("Birthday slides created")
        if anniversaries:
            create_and_populate_slides(presentation_id=presentation_id, layout="Anniversary", names_obj=anniversaries)
            print("Anniversary slides created")
    except Exception as e:
        print(f"Error creating slides: {e}")
        pass    
    try:
        export_pdf(presentation_id=presentation_id, pdf_name=f"birthday_anniversary_{current_time}.pdf")
        if export_images:
            export_slide_images(presentation_id=presentation_id)
    except Exception as e:
        print(f"Error exporting PDF/images: {e}")
        pass

# def generate_obituary_slides(template_ppt_id, sub_folder_id, export_images=False):    
#     global slides_service, drive_service, current_time    
#     # Get obituaries from google sheet
#     try:
#         obituaries = get_obituaries()        
#     except Exception as e:
#         print(f"Error getting obituary data from google sheet: {e}")
#         pass
#     if obituaries:
#         try:
#             # copy from template to the new folder
#             presentation_id = drive_copy_file(drive_service, template_ppt_id, sub_folder_id, f"obituary_{current_time}")
#             slides_service.presentations().get(presentationId=presentation_id).execute()        
#             create_and_populate_slides_obituary(presentation_id=presentation_id, data=obituaries)
#             print("Obituary slides created")
#             export_pdf(presentation_id=presentation_id, pdf_name=f"obituary_{current_time}.pdf")
#             if export_images:
#                 export_slide_images(presentation_id=presentation_id)
#         except Exception as e:
#             print(f"Error creating obituary slides: {e}")
#             pass

# split the long slides text into multiple slides.(only for Text and TextAndImage layouts)
def split_long_announcement_text(data:list[models.Announcement]):
    right_sized_announcements:list[models.Announcement] = []
    for item in data:
        try:
            text = item.text
            layout = item.announcement_type.name            
            if layout.lower() in ["text", "textandimage"] and get_effective_lines(text, layout) > layout_config[layout]["linesPerSlide"]:                
                text_chunks = split_text_into_slides(text,item.title,layout)
                for chunk in text_chunks:
                    right_sized_announcements.append(models.Announcement(chunk['layout'], chunk['title'], chunk['text'], item.image_url))
            else:
                right_sized_announcements.append(item)
        except Exception as e:
            print(f"Error in split_long_announcement_text: {e}")
            right_sized_announcements.append(item)

    return right_sized_announcements


# generate announcements slides. for one row one slide. the layout based on the type of announcementz
def generate_announcements_slides(template_ppt_id, sub_folder_id, export_images=False):
    global slides_service, drive_service, current_time
    # Get announcements from DB
    try:
        announcements = get_announcements()
    except Exception as e:
        print(f"Error getting announcements from DB: {e}")
        pass
    if announcements:
        try:
            try:
                announcements = split_long_announcement_text(announcements)
            except Exception as e:
                pass
            # copy from template to the new folder
            presentation_id = drive_copy_file(drive_service, template_ppt_id, sub_folder_id, f"announcements_{current_time}")
            slides_service.presentations().get(presentationId=presentation_id).execute()
            create_and_populate_slides_announcements(presentation_id=presentation_id, data=announcements)
            print("Announcements slides created")
            export_pdf(presentation_id=presentation_id, pdf_name=f"announcements_{current_time}.pdf")
            if export_images:
                export_slide_images(presentation_id=presentation_id)
        except Exception as e:
            print(f"Error creating announcements slides: {e}")
            pass

# main
def main():    
    global slides_service, drive_service, current_time, sub_folder_id, layouts
    slides_service = build("slides", "v1", credentials=credentials)
    drive_service = build("drive", "v3", credentials=credentials)
    # if a parameter --auto is passed, then run the script in auto mode
    #get parameter
    trigger = False
    # all_slides = True
    announcements_only = False
    birthday_anniversary_only = False
    export_images = False

    # check all parameters and set flags
    for arg in sys.argv:
        if arg == "--bdays":
            birthday_anniversary_only = True
        if arg == "--announcements":
            announcements_only = True
        if arg == "--images":
            export_images = True
    
    # if trigger:
    #     if not get_manual_triggers():
    #         print("No manual trigger found. Exiting...")
    #         exit()
    #     else:
    #         print("Manual trigger found. ")
    #         update_manual_trigger()
    
    # time.sleep(15) 
    dt = datetime.now()
    current_time = dt.strftime("%d%m%y_%H%M%S")
    sub_folder_name = dt.strftime("%Y-%m-%d")

    # create a google drive folder in the  output folder with todays date, if not already exists
    sub_folder_id = drive_check_folder_exists(drive_service, sub_folder_name, output_folder_id)
    if not sub_folder_id:
        # create the folder
        sub_folder_id = drive_create_folder(drive_service, sub_folder_name, output_folder_id)

    # generate the slides
    if not announcements_only:
        generate_birthdays_anniversaries_slides(template_ppt_id, sub_folder_id, export_images)
    
    if not birthday_anniversary_only:
        generate_announcements_slides(template_ppt_id, sub_folder_id, export_images)
    # generate_obituary_slides(template_ppt_id, sub_folder_id, export_images)
    
# main function
if __name__ == "__main__":
    main()