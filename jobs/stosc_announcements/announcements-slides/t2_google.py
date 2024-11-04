# Import the Google API client library
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

# Define the scopes for the Slides and Drive APIs
SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']

# The ID of the presentation to modify
PRESENTATION_ID = '1ZuSVD5zJwUWxSOaANPB7Eyk5KVVsI3FELZR2aNE7jiM'

# The name of the theme and layout to use
THEME_NAME = 'STOSC'
LAYOUT_NAME = 'CUSTOM'

# The text to insert in the placeholder
TEXT = 'Hello world'

# Create the credentials object from a service account file
creds = Credentials.from_service_account_file("google_service_account.json", scopes=SCOPES)
service = build('slides', 'v1', credentials=creds)

# Get the presentation and find the theme and layout IDs
presentation = service.presentations().get(presentationId=PRESENTATION_ID).execute()
layout_id = "g240b39cca13_0_0"

for layout in presentation['layouts']:
    # Check each layout's name
    if layout['layoutProperties']['name'] == LAYOUT_NAME:
        # Found the layout ID
        layout_id = layout['objectId']
        break

if layout_id is None:
    # Layout not found, raise an error
    raise ValueError(f'Layout {LAYOUT_NAME} not found in theme {THEME_NAME}')

# Create a new slide with the theme and layout IDs
requests = []
requests.append({
    'createSlide': {
        'slideLayoutReference': {
            'layoutId': layout_id            
        },
        'placeholderIdMappings': [
            {
                'layoutPlaceholder': {
                    'type': 'BODY',
                    'index': 0
                },
                'objectId': 'g240b39cca13_1_0'
            }
        ]
    }
})

# Insert the text in the placeholder
requests.append({
    'insertText': {
        'objectId': 'g240b39cca13_1_0',
        'text': TEXT,
        'insertionIndex': 0
    }
})

# Execute the requests
response = service.presentations().batchUpdate(presentationId=PRESENTATION_ID, body={'requests': requests}).execute()
print(f'Created slide with ID: {response["replies"][0]["createSlide"]["objectId"]}')
