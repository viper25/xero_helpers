# create enum announcement type(Text, Obituary, image, text+Image)
from enum import Enum

class Layouts(str, Enum):
    Birthday = "Birthday"
    Anniversary = "Anniversary"
    Text = "Text"
    Obituary = "Obituary"
    Image = "Image"
    TextAndImage = "TextAndImage"
    
class NamesList():  
    def __init__(self, date_range:str, data:list[str]):
        self.date_range = date_range
        self.data = data

class Obituaries():
    def __init__(self, text:str, image_url:str):
        self.text = text
        self.image_url = image_url

class Announcement():
    def __init__(self, announcement_type:Layouts, title:str, text:str, image_url:str ):
        self.announcement_type = announcement_type
        self.title = title
        self.text = text
        self.image_url = image_url
    
class CombinedData():
    def __init__(self, birthdays:NamesList=None, anniversaries:NamesList=None, obituaries:Obituaries=None):
        self.birthdays = birthdays
        self.anniversaries = anniversaries
        self.obituaries = obituaries