import logging

import mysql.connector
import pendulum
from colorit import *
from dotenv import load_dotenv

load_dotenv()
init_colorit()

DB_USER = os.getenv("STOSC_DB_USER")
DB_PASSWORD = os.getenv("STOSC_DB_WRITE_PWD")
DB_HOST = os.getenv("STOSC_DB_HOST")
DB_PORT = 3306
LOGLEVEL = 'INFO'

# ----------------------------------------------------------------------------------------------------------------------
# Module logger
logger = logging.getLogger('DB')
logger.setLevel(level=LOGLEVEL)

# ----------------------------------------------------------------------------------------------------------------------


def __db_executeQuery(sql: str, prepared=False, *args):
    # Connect to MariaDB Platform
    logger.debug(f"Query: [{sql}] on DB: [stosc_churchcrm]")
    print(color(f"Connecting to {DB_USER}@{DB_HOST}:{DB_PORT}", Colors.green))
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='stosc_churchcrm'
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


def get_bday(duration: str = 'w'):
    today = pendulum.now("Asia/Singapore")
    print(color(f"Today: {today}", Colors.green))
    if (duration.lower()) == "d":
        start = today.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
    else:
        start = today.start_of('week').strftime("%Y%m%d")
        end = today.end_of('week').strftime("%Y%m%d")

    sql_today = f"SELECT left(right(fam_Name,5),4) as code, concat(per_firstname, ' ', per_lastname) AS NAME, concat_ws('/', `per_birthday`, `per_birthmonth`, `per_birthyear`) AS birthday, concat( year(CURRENT_DATE) - per_birthyear - 1, ' Yrs') AS 'Age'FROM `person_per`JOIN   `family_fam`ON family_fam.fam_id=person_per.per_fam_id where  `per_birthday` IS NOT null and `per_birthmonth` IS NOT null and per_cls_id <> 4 AND fam_datedeactivated IS null and person_per.per_cls_id != 4 and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(  date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(concat('2000', lpad(per_birthmonth, 2, '0'), lpad(per_birthday, 2, '0')), '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY `per_birthmonth`, `per_birthday`"

    _result = __db_executeQuery(sql_today)
    return _result


def get_anniversaries(duration: str = 'w'):
    today = pendulum.now("Asia/Singapore")
    if (duration.lower()) == "d":
        start = today.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
    else:
        start = today.start_of('week').strftime("%Y%m%d")
        end = today.end_of('week').strftime("%Y%m%d")

    sql = f"SELECT left(right(fam_Name,5),4) as code, concat(hof.per_firstname, ' ', hof.per_lastname, ' & ', spouse.per_firstname, ' ', spouse.per_lastname) AS NAME, fam_weddingdate AS weddingdate FROM `family_fam`JOIN (SELECT * FROM `person_per` WHERE  per_fmr_id=1 AND per_id NOT IN ( SELECT r2p_record_id FROM   record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND per_cls_id <> 4) hof on fam_id=hof.per_fam_id join (SELECT * FROM   `person_per` WHERE  per_fmr_id=2 AND per_id NOT IN ( SELECT r2p_record_id FROM record2property_r2p WHERE  record2property_r2p.r2p_pro_id=12) AND    per_cls_id <> 4) spouse on fam_id=spouse.per_fam_id where  fam_datedeactivated IS null and if(date_format({start}, '%m%d') > date_format({end}, '%m%d'), (date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')AND'1231')OR(date_format(fam_weddingdate, '%m%d') BETWEEN '0101'  AND  date_format({end}, '%m%d')), date_format(fam_weddingdate, '%m%d') BETWEEN date_format({start}, '%m%d')and date_format({end}, '%m%d') ) ORDER BY date_format(fam_weddingdate, '%m%d') ASC"

    _result = __db_executeQuery(sql)
    return _result
