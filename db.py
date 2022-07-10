import os
import mysql.connector
import pendulum
import enum
import logging
from dotenv import load_dotenv
from colorit import *

load_dotenv()

init_colorit()


USER="tempwrite"
PASSWORD=os.environ.get('STOSC_DB_WRITE_PWD')
HOST=os.environ.get('STOSC_DB_HOST')
PORT=3306

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
def update_gb_eligibility(member, eligibility):
    sql_check = "SELECT fc.c5, fc.c7 FROM family_custom fc where fc.c7 = %s"
    crm_is_eligible = __db_executeQuery(sql_check, Databases.CRM, True, member)[0][0].lower() == 'true'
    if crm_is_eligible == eligibility:
        return
    sql = "update family_custom fc set fc.c5 = %s where fc.c7 = %s"
    print(color(f"\t   ✏️ Changing {member} eligibility from {crm_is_eligible} to {eligibility}",Colors.orange))
    _result = __db_executeQuery(sql, Databases.CRM, True, str(eligibility), member)
    return _result