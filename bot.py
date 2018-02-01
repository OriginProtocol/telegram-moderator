# -*- coding: utf-8 -*-

"""Group Chat Logger

This bot is a modified version of the echo2 bot found here:
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py

This bot logs all messages sent in a Telegram Group to a database.

"""

from __future__ import print_function
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from model import User, Message, session
from time import strftime
import re

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def security_check_message(bot, update):
    """ Test message for security violations """

    r = re.compile(r'FART')
    if r.match(update.message.text):
        print("Matched!")
        # Delete the message
        update.message.delete()

        # # Ban the user
        # kick_success = update.message.chat.kick_member(update.message.from_user.id)
        # print(kick_success)


def logger(bot, update):
    """Primary Logger. Handles incoming bot messages and saves them to DB"""

    user = update.message.from_user

    if id_exists(user.id) == True:
        log_message(user.id, update.message.text)
    else:
        add_user_success = add_user(user.id, user.first_name, user.last_name, user.username)

        if add_user_success == True:
            log_message(user.id, update.message.text)
            print("User added: {}".format(user.id))
        else:
            print("Something went wrong adding the user {}".format(user.id), file=sys.stderr)

    if update.message.text:
        print("{} {} ({}) : {}".format(
            strftime("%Y-%m-%dT%H:%M:%S"),
            user.id,
            (user.username or (user.first_name + " " + user.last_name) or "").encode('utf-8'),
            update.message.text.encode('utf-8'))
        )

    try:
        security_check_message(bot, update)
    except Exception as e:
        print(e)


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
    print("Update '{}' caused error '{}'".format(update, error), file=sys.stderr)


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
