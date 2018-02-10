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
from model import User, Message, MessageHide, UserBan, session
from time import strftime
import re
import unidecode


class TelegramMonitorBot:

    def __init__(self):
        self.debug = os.environ.get('DEBUG') is not None

        self.safe_user_ids = map(int, os.environ['SAFE_USER_IDS'].split(','))

        self.message_ban_patterns = os.environ['MESSAGE_BAN_PATTERNS']
        self.message_ban_re = re.compile(
            self.message_ban_patterns,
            re.IGNORECASE | re.VERBOSE)
            if self.message_ban_patterns else None

        self.message_hide_patterns = os.environ['MESSAGE_HIDE_PATTERNS']
        self.message_hide_re = re.compile(
            self.message_hide_patterns,
            re.IGNORECASE | re.VERBOSE)
            if self.message_hide_patterns else None

        self.name_ban_patterns = os.environ['NAME_BAN_PATTERNS']
        self.name_ban_re = re.compile(
            self.name_ban_patterns,
            re.IGNORECASE | re.VERBOSE)
            if self.name_ban_patterns else None


    def ban_user(self, update):
        """ Ban user """
        kick_success = update.message.chat.kick_member(update.message.from_user.id)


    def security_check_username(self, bot, update):
        """ Test username for security violations """

        full_name = (update.message.from_user.first_name + " "
            + update.message.from_user.last_name)
        if self.name_ban_re and self.name_ban_re.search(full_name):
            # Ban the user
            if self.debug:
                update.message.reply_text("DEBUG: Ban match full name: {}".format(full_name.encode('utf-8')))
            print("Ban match full name: {}".format(full_name.encode('utf-8')))
            self.ban_user(update)

        if self.name_ban_re and self.name_ban_re.search(update.message.from_user.username or ''):
            # Ban the user
            if self.debug:
                update.message.reply_text("DEBUG: Ban match username: {}".format(update.message.from_user.username.encode('utf-8')))
            print("Ban match username: {}".format(update.message.from_user.username.encode('utf-8')))
            self.ban_user(update)


    def security_check_message(self, bot, update):
        """ Test message for security violations """

        # Remove accents from letters (é->e, ñ->n, etc...)
        message = unidecode.unidecode(update.message.text)
        # TODO: Replace lookalike unicode characters

        if self.message_hide_re and self.message_hide_re.search(message):
            # Delete the message
            if self.debug:
                update.message.reply_text("DEBUG: Hide match: {}".format(update.message.text.encode('utf-8')))
            print("Hide match: {}".format(update.message.text.encode('utf-8')))
            update.message.delete()
            # Log in database
            s = session()
            messageHide = MessageHide(
                user_id=update.message.from_user.id,
                message=update.message.text)
            s.add(messageHide)
            s.commit()
            s.close()

        if self.message_ban_re and self.message_ban_re.search(message):
            # Ban the user
            if self.debug:
                update.message.reply_text("DEBUG: Ban message match: {}".format(update.message.text.encode('utf-8')))
            print("Ban message match: {}".format(update.message.text.encode('utf-8')))
            # Ban the user
            self.ban_user(update)
            # Any message that causes a ban gets deleted
            update.message.delete()
            # Log in database
            s = session()
            userBan = UserBan(
                user_id=update.message.from_user.id,
                reason=update.message.text)
            s.add(userBan)
            s.commit()
            s.close()


    def logger(self, bot, update):
        """Primary Logger. Handles incoming bot messages and saves them to DB"""
        try:
            user = update.message.from_user

            if self.id_exists(user.id):
                self.log_message(user.id, update.message.text)
            else:
                add_user_success = self.add_user(
                    user.id,
                    user.first_name,
                    user.last_name,
                    user.username)

                if add_user_success:
                    self.log_message(user.id, update.message.text)
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

            if not update.message.from_user.id in self.safe_user_ids:
                # Security checks
                self.security_check_username(bot, update)
                self.security_check_message(bot, update)

        except Exception as e:
            print(e)


    # DB queries
    def id_exists(self, id_value):
        s = session()
        bool_set = False
        for id1 in s.query(User.id).filter_by(id=id_value):
            if id1:
                bool_set = True

        s.close()

        return bool_set


    def log_message(self, user_id, user_message):
        try:
            s = session()
            msg1 = Message(user_id=user_id, message=user_message)
            s.add(msg1)
            s.commit()
            s.close()
        except Exception as e:
            print(e)


    def add_user(self, user_id, first_name, last_name, username):
        try:
            s = session()
            user = User(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username)
            s.add(user)
            s.commit()
            s.close()
            return id_exists(user_id)
        except Exception as e:
            print(e)


    def error(self, bot, update, error):
        """Log Errors caused by Updates."""
        print("Update '{}' caused error '{}'".format(update, error),
            file=sys.stderr)


    def start(self):
        """Start the bot."""

        # Create the EventHandler and pass it your bot's token.
        updater = Updater(os.environ["TELEGRAM_BOT_TOKEN"])

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(
            Filters.text,
            lambda bot, update : self.logger(bot, update)
        ))

        # dp.add_handler(MessageHandler(Filters.status_update, status))

        # log all errors
        dp.add_error_handler(
            lambda bot, update, error : self.error(bot, update, error)
        )

        # Start the Bot
        updater.start_polling()

        print("Bot started")

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


if __name__ == '__main__':
    c = TelegramMonitorBot()

    c.start()
