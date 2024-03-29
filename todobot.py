import json  # parse JSON responses from Telegram to Python dictionaries
import time
import urllib
from apscheduler.schedulers.background import BackgroundScheduler

import requests  # web requests to interact with telegram API

from config import token
from dbsetup import Databasesetup

db = Databasesetup("./todo.sqlite")

TOKEN = token
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
NAME = "productiveme_bot"


def get_json_from_url(url):  # gets JSON from Telegram API url
    content = requests.get(url).content.decode("utf8")
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)

    js = get_json_from_url(url)  # list of updates in JSON format retrieved from API
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def handle_update(update):
    chat = None
    text = None
    if "message" in update:
        if "text" in update["message"]:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
        else:
            chat = None
    elif "callback_query" in update:
        if "data" in update["callback_query"]:
            text = update["callback_query"]["data"]
            chat = update["callback_query"]["message"]["chat"]["id"]
        else:
            chat = None
    if chat is not None:
        items = db.get_items(chat)
        if text == "/done":
            if not items:
                send_message("*🐨There are no goals at the moment. Start with typing anything below!*", chat)
            else:
                message = ""
                items = db.get_items(chat)
                keyboard = build_keyboard(items)
                send_message(
                    "*🔥Congrats on completing the goal! Select an item to delete from the inline keyboard:*" + message,
                    chat, keyboard)
        elif any(text in s for s in items):  # if user already sent this goal
            db.delete_item(text, chat)
            items = db.get_items(chat)

            if not items:
                send_message("*✅Another goal done!\nThere are no current goals at the moment. Well done🔥!*", chat)
            else:
                completedItems = db.get_completed_items(chat)
                completedItems = ["☑" + sub for sub in completedItems]
                message = "\n️".join(completedItems)
                keyboard = build_keyboard(items)
                send_message("*✅Another goal done!  Completed goals today: \n*" + message + "\nMain Goals for today:", chat, keyboard)

        elif not any(text in s for s in items) and (not text.startswith("/") and (text != "~")):  # if user didn't send it
            if len(db.get_items(chat)) >= 3:
                items = db.get_items(chat)
                keyboard = build_keyboard(items)
                send_message("*There could be only Three \nMain Goals for today! \n*", chat, keyboard)
                return
            db.add_item(text, chat)
            items = db.get_items(chat)
            keyboard = build_keyboard(items)
            completedItems = db.get_completed_items(chat)
            completedItems = ["☑" + sub for sub in completedItems]
            message = "\n".join(completedItems)
            send_message("*✍New goal added. Completed goals today: \n*" + message + "\nMain Goals for today:", chat, keyboard)


        elif text == "/start":
            keyboard = build_keyboard(items)
            send_message("*🗒️Welcome to your personal Three Main Goals! \n\nTo add the goal, just type it below⬇️ "
                         "\n\nDelete your goal using inline menu or just type /done to remove it."
                         "\n\nUse /currentgoals to list your goals"
                         " To clear your list, send /clear. \n\nThank you! Message @alexff91 if you have any questions.*",
                         chat, keyboard)
            completedItems = db.get_completed_items(chat)
            completedItems = ["☑" + sub for sub in completedItems]
            message = "\n".join(completedItems)
            send_message("*🎯Completed goals today: \n*" + message + "\nMain Goals for today:", chat)

        elif text == "/statistics":
            send_message("*Here is your statistics*",
                         chat)
            itemsWeekly = db.get_statistics_weekly(chat)
            itemsAll = db.get_statistics_all(chat)
            completedItems = ["Total number of completed goals: " + str(sub) for sub in itemsAll]
            completedItemsWeekly = ["\nWeekly number of completed goals: " + str(sub) for sub in itemsWeekly]
            message = "\n".join(completedItems) + "\n".join(completedItemsWeekly)
            send_message("🎯" + message + "\nGood Woork!", chat)

        elif text == "/currentgoals":
            keyboard = build_keyboard(items)
            completedItems = db.get_completed_items(chat)
            completedItems = ["☑" + sub for sub in completedItems]
            message = "\n".join(completedItems)
            if len(items) > 0:
                send_message("*🎯 Completed goals today: \n*" + message + "\nMain Goals for today:", chat, keyboard)
            else:
                send_message("*🎯All goals are complete for today! \n*" + message, chat, keyboard)

        elif text == "/help":
            send_message("*🗒️Welcome to your personal todo list! \n\nTo add the goal, just type it below⬇️ "
                         "\n\nDelete your goal using inline menu or just type /done to remove it."
                         "\n\nUse /currentgoals to list your goals"
                         " To clear your list, send /clear. \n\nThank you! Message @alexff91 if you have any questions.*",
                         chat)

        elif text == "/clear":
            db.delete_all(text, chat)
            items = db.get_items(chat)
            keyboard = build_keyboard(items)
            completedItems = db.get_completed_items(chat)
            completedItems = ["☑" + sub for sub in completedItems]
            message = "\n".join(completedItems)
            send_message("*✅✅✅Well done!\nNow there are no goals at the moment*\n" + message, chat)

        # elif text.startswith("/"):
        # continue


def handle_updates(updates):
    for update in updates["result"]:
        handle_update(update)


def get_last_chat_id_and_text(updates: {}):  # only last message instead of whole bunch of updates
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return text, chat_id


def build_keyboard(items):
    keyboard = [[{"text": item, "callback_data": item[:34]}] for item in items]
    reply_markup = {"inline_keyboard": keyboard}
    return json.dumps(reply_markup)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    requests.get(url).content.decode("utf8")

def auto_send_start():
    users = db.get_users()
    for user in users:
        send_message("Time to fill your goals!", user)
    return 0


def auto_send_end():
    users = db.get_users()
    for user in users:
        items = db.get_items(user)
        keyboard = build_keyboard(items)
        completedItems = db.get_completed_items(user)
        message = "\n".join(completedItems)
        send_message("*Time to check your goals.  Completed goals today: \n*" + message + "\nMain Goals for today:", user, keyboard)
    return 0

def main():
    db.setup()
    last_update_id = None
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_send_start, 'cron', hour='6', misfire_grace_time=3600)
    scheduler.add_job(auto_send_end,  'cron', hour='17', misfire_grace_time=3600)
    scheduler.start()
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
