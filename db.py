import mysql.connector
import enum
import logging
from dotenv import load_dotenv
from colorit import *
import tomllib

init_colorit()

# Load config
with open("config.toml", "rb") as f:
    config = tomllib.load(f)

USER = config['database']['USER']
PASSWORD = config['database']['STOSC_DB_WRITE_PWD']
HOST = config['database']['STOSC_DB_HOST']
PORT = 3306

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger=logging.getLogger(__name__)

class Databases(enum.Enum):
    CRM='stosc_churchcrm'
    FORMS='forms_db'

# Execute Query and return data
def __db_executeQuery(sql, db, prepared=False, *args):
    # Connect to MariaDB Platform
    try:
        conn = mysql.connector.connect( 
            user = USER, 
            password = PASSWORD, 
            host = HOST, 
            port = PORT, 
            database = db.value
        )
    except Exception as e:
        logger.error(e)
        raise
    try:
        if prepared:
            # Get Cursor 
            with conn.cursor(prepared=True) as cursor:
                cursor.execute(sql, args)
                _result = cursor.fetchall()
        else:
            # Get Cursor 
            with conn.cursor() as cursor:
                cursor.execute(sql)
                _result = cursor.fetchall()
        return _result
    except Exception as e:
        logger.error(e)
    finally:
        # Close Connection
        conn.close()   

# ----------------------------------------------------------------------------------------------------------------------
def update_gb_eligibility(member, current_eligibility_status, members_status_change_eligible, members_status_change_ineligible):
    sql_check = "SELECT fc.c5, fc.c7 FROM family_custom fc where fc.c7 = %s"
    _x = __db_executeQuery(sql_check, Databases.CRM, True, member)
    if _x:
        if _x[0][0]:
            crm_is_eligible = _x[0][0].lower() == 'true'
        else:
            crm_is_eligible = False
        if crm_is_eligible == current_eligibility_status:
            return
        else:
            sql = "update family_custom fc set fc.c5 = %s where fc.c7 = %s"
            print(color(f"\t   ✏️ Changing {member} eligibility from {crm_is_eligible} to {current_eligibility_status}",Colors.orange))
            # Add member to a set of members to be updated
            if current_eligibility_status:
                members_status_change_eligible.add(member)
            else:
                members_status_change_ineligible.add(member)
            _result = __db_executeQuery(sql, Databases.CRM, True, str(current_eligibility_status), member)
            return None
    else:
        print(color(f"\t   ⚠️ {member} not found in CRM",Colors.red))
        return None

def get_address(member_code: str):
    sql = "select f.fam_Zip from family_fam f where SUBSTRING(f.fam_Name,POSITION('(' IN f.fam_Name)+1,4) = %s"
    _result = __db_executeQuery(sql, Databases.CRM, True, member_code)
    return _result[0][0]

def get_email(member_code: str):
    sql = "select fam_Email from family_fam f where SUBSTRING(f.fam_Name,POSITION('(' IN f.fam_Name)+1,4) = %s"
    _result = __db_executeQuery(sql, Databases.CRM, True, member_code)
    return _result[0][0]

def get_zip_lat_lon(member_code: str):
    sql = "select fam_latitude, fam_longitude, fam_zip from family_fam f where SUBSTRING(f.fam_Name,POSITION('(' IN f.fam_Name)+1,4) = %s"
    _result = __db_executeQuery(sql, Databases.CRM, True, member_code)
    return _result[0][0], _result[0][1], _result[0][2]


def update_lat_lon(memberCode, sla_lat, sla_lon):
    sql = "update family_fam f set f.fam_latitude = %s, f.fam_longitude=%s where SUBSTRING(f.fam_Name,POSITION('(' IN f.fam_Name)+1,4) = %s"
    _result = __db_executeQuery(sql, Databases.CRM, True, sla_lat, sla_lon, memberCode)
    return _result