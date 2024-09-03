import requests
from colorit import *
from dotenv import load_dotenv

import db

load_dotenv()
init_colorit()

TELEGRAM_IDS = os.getenv("TELEGRAM_IDS")
TELEGRAM_SEND_MSG_URL = os.getenv("TELEGRAM_SEND_MSG_URL")


def get_bday_list():
    print(color(f"Getting today's Birthdays", Colors.white))

    bdays_today = db.get_bday('d')
    return bdays_today


def get_anniversary_list():
    print(color(f"Getting today's Anniversaries", Colors.white))

    anniversaries_today = db.get_anniversaries('d')
    return anniversaries_today


def send_telegram_message(msg: str = "No Birthdays or Anniversaries today"):

    for id in TELEGRAM_IDS.split(','):
        payload = {
            "text": msg.encode("utf8"),
            "parse_mode": "MarkdownV2",
            "chat_id": id

        }
        # Posting the payload to Telegram Bot API
        print(color(f"Sending message to Telegram ID: {id}", Colors.green))
        requests.post(TELEGRAM_SEND_MSG_URL, payload)


def create_msg(bdays, anniversaries):
    # Create Telegram message based on bdays and anniversaries
    _msg = "*__Daily Notifications__* 📅\n\n"
    if len(bdays) > 0:
        _msg += ">*Birthdays today* 🎂\n"
        for _item in bdays:
            _msg += f"•** {_item[1].strip()}** `({_item[0].strip()})`\n"
        _msg += "\n"
    else:
        _msg += "`No Birthdays today`\n"

    if len(anniversaries) > 0:
        _msg += ">*Wedding Anniversaries today* 💍\n"
        for _item in anniversaries:
            _msg += f"•** {_item[1].strip()}** `({_item[0].strip()})`\n"
        _msg += "\n"
    else:
        _msg += "`No Anniversaries today`"

    return _msg


if __name__ == "__main__":
    bdays = get_bday_list()
    anniversaries = get_anniversary_list()
    telegram_msg = create_msg(bdays, anniversaries)
    send_telegram_message(telegram_msg)
