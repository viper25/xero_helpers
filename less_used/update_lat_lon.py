import tomllib

import requests
from colorit import *

import db

init_colorit()

# Load config
with open("config.toml", "rb") as f:
    config = tomllib.load(f)


def get_zip_from_onemap(zip):
    try:
        new_url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={zip}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
        result = requests.get(new_url).json()
        if len(result['results']) > 0:
            lat, lon = result['results'][0]['LATITUDE'], result['results'][0]['LONGITUDE']
            return lat, lon
    except Exception as e:
        print(color(f"Error in OneMap: {e}", Colors.red))


FILE_MEMBERS = config['gb_eligibility']['FILE_MEMBERS']

# Loop through active users in CRM
with open(FILE_MEMBERS, "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("memberCode"):
            continue
        if line:
            memberCode, Name, contactID = line.split(",")
            if memberCode == 'C000':
                continue
            # print(f"{Fore.WHITE}Comparing addresses for {Name} ({memberCode})")
            lat, lon, zip = db.get_zip_lat_lon(memberCode)
            if lat == 0.0 or lon == 0.0:
                sla_lat, sla_lon = get_zip_from_onemap(zip)
                result = db.update_lat_lon(memberCode, sla_lat, sla_lon)
                print(color(f"{memberCode} has been updated with lat: {sla_lat} and lon: {sla_lon}", Colors.green))

