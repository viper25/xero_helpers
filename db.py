import mysql.connector
import enum
import logging
from dotenv import load_dotenv
from colorit import *
import tomli

init_colorit()

# Load config
with open("config.toml", "rb") as f:
    config = tomli.load(f)

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
    crm_is_eligible = __db_executeQuery(sql_check, Databases.CRM, True, member)[0][0].lower() == 'true'
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