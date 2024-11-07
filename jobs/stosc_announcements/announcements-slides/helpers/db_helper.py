import os
import mysql.connector
import pendulum
from dotenv import load_dotenv
import models.models as models

load_dotenv()

USER = os.environ.get('stosc_crm_db_user')
PASSWORD = os.environ.get('stosc_crm_db_password')
HOST = os.environ.get('stosc_crm_db_host')
DBNAME = os.environ.get('stosc_crm_db_name')
PORT = 3306


# Execute Query and return data
def __db_executeQuery(sql: str, prepared=False, *args):
    # Connect to MariaDB Platform    
    try:
        conn = mysql.connector.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            database=DBNAME,
        )
    except Exception as e:
        print(e)
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
        print(e)
    finally:
        # Close Connection
        conn.close()
    # ----------------------------------------------------------------------------------------------------------------------


def get_birthdays(duration: str = 'w')->models.NamesList:
    today = pendulum.now("Asia/Singapore")
    if (duration.lower()) == "d":
        start = today.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
    else:
        start = today.start_of('week').strftime("%Y%m%d")
        end = today.end_of('week').strftime("%Y%m%d")

    sql = f"SELECT left(right(fam_Name,5),4) as code, concat(per_firstname, ' ', per_lastname) AS NAME, concat_ws('/', `per_birthday`, `per_birthmonth`, `per_birthyear`) AS birthday, concat( year(CURRENT_DATE) - per_birthyear - 1, ' Yrs') AS 'Age'FROM `person_per`JOIN   `family_fam`ON family_fam.fam_id=person_per.per_fam_id where  `per_birthday` IS NOT null and `per_birthmonth` IS NOT null and per_cls_id <> 4 AND fam_datedeactivated IS null and person_per.per_cls_id != 4 and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(  date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY `per_birthmonth`, `per_birthday`"

    _result = __db_executeQuery(sql)
    # return date range in the following format: "Aug 21 - Aug 27, 2023" and the _result
    date_range = today.start_of('week').strftime("%b %d") + " - " +  today.end_of('week').strftime("%b %d, %Y")
    result =  [f"{row[1]} ({row[0]})" for row in _result]
    # return class models.Birthdays
    return models.NamesList(date_range, result)

# ----------------------------------------------------------------------------------------------------------------------
def get_anniversaries(duration: str = 'w')->models.NamesList:
    today = pendulum.now("Asia/Singapore")
    if (duration.lower()) == "d":
        start = today.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
    else:
        start = today.start_of('week').strftime("%Y%m%d")
        end = today.end_of('week').strftime("%Y%m%d")

    sql = f"SELECT left(right(fam_Name,5),4) as code, concat(hof.per_firstname, ' ', hof.per_lastname, ' & ', spouse.per_firstname, ' ', spouse.per_lastname) AS NAME, fam_weddingdate AS weddingdate FROM `family_fam`JOIN (SELECT * FROM `person_per` WHERE  per_fmr_id=1 AND per_id NOT IN ( SELECT r2p_record_id FROM   record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND per_cls_id <> 4) hof on fam_id=hof.per_fam_id join (SELECT * FROM   `person_per` WHERE  per_fmr_id=2 AND per_id NOT IN ( SELECT r2p_record_id FROM record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND    per_cls_id <> 4) spouse on fam_id=spouse.per_fam_id where  fam_datedeactivated IS null and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(date_format(fam_weddingdate, '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY date_format(fam_weddingdate, '%m%d') ASC"

    _result = __db_executeQuery(sql)
    date_range = today.start_of('week').strftime("%b %d") + " - " +  today.end_of('week').strftime("%b %d, %Y")
    result =  [f"{row[1]} ({row[0]})" for row in _result]
    # return class models.Anniversaries
    return models.NamesList(date_range, result) 

# ----------------------------------------------------------------------------------------------------------------------