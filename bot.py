# -*- coding: utf-8 -*-

"""Group Chat Logger

This bot is a modified version of the echo2 bot found here:
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py

This bot logs all messages sent in a Telegram Group to a database.

"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os
from model import User, Message, session

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.

def logger(bot, update):
    """Primary Logger. Handles incoming bot messages and saves them to DB"""

    user = update.message.from_user

    if id_exists(user.id) == True:
        log_message(user.id, update.message.text)
    else:
        add_user_success = add_user(user.id, user.first_name, user.last_name, user.username)

        if add_user_success == True:
            log_message(user.id, update.message.text)
            print("User added")
        else:
            print("Something went wrong adding the user {}".format(user.id))

    print("{} : {}".format(user.username.encode('utf-8'),update.message.text.encode('utf-8')))

# DB queries

def id_exists(id_value):
    s = session()
    bool_set = False
    for id1 in s.query(User.id).filter_by(id=id_value):
        if id1:
            bool_set = True

    s.close()

    return bool_set

def log_message(user_id, user_message):

    try:
        s = session()
        msg1 = Message(user_id=user_id,message=user_message)
        s.add(msg1)
        s.commit()
        s.close()

    except Exception as e:
        print(e)

def add_user(user_id, first_name, last_name, username):
    try:
        s = session()
        bool_set = False
        user = User(id=user_id, first_name = first_name, last_name = last_name, username = username)
        s.add(user)
        s.commit()
        s.close()

        if id_exists(user_id) == True:
            bool_set = True

        return bool_set

    except Exception as e:
        print(e)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(os.environ["TELEGRAM_BOT_TOKEN"])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, logger))

    # dp.add_handler(MessageHandler(Filters.status_update, status))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    print("Bot started")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
