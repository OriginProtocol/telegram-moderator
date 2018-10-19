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
from mwt import MWT

class TelegramMonitorBot:


    def __init__(self):
        self.debug = (
            (os.environ.get('DEBUG') is not None) and
            (os.environ.get('DEBUG').upper() != "false"))

        # Are admins exempt from having messages checked?
        self.admin_exempt = (
            (os.environ.get('ADMIN_EXEMPT') is not None) and
            (os.environ.get('ADMIN_EXEMPT').upper() != "false"))

        if (self.debug):
            print("🔵 debug:", self.debug)
            print("🔵 admin_exempt:", self.admin_exempt)
            print("🔵 TELEGRAM_BOT_POSTGRES_URL:", os.environ["TELEGRAM_BOT_POSTGRES_URL"])
            print("🔵 TELEGRAM_BOT_TOKEN:", os.environ["TELEGRAM_BOT_TOKEN"])
            print("🔵 NOTIFY_CHAT:", os.environ['NOTIFY_CHAT'] if 'NOTIFY_CHAT' in os.environ else "<undefined>")
            print("🔵 MESSAGE_BAN_PATTERNS:\n", os.environ['MESSAGE_BAN_PATTERNS'])
            print("🔵 MESSAGE_HIDE_PATTERNS:\n", os.environ['MESSAGE_HIDE_PATTERNS'])
            print("🔵 NAME_BAN_PATTERNS:\n", os.environ['NAME_BAN_PATTERNS'])

        # Channel to notify of violoations, e.g. '@channelname'
        self.notify_chat = os.environ['NOTIFY_CHAT'] if 'NOTIFY_CHAT' in os.environ else None

        # List of chat ids that bot should monitor
        self.chat_ids = (
            list(map(int, os.environ['CHAT_IDS'].split(',')))
            if "CHAT_IDS" in os.environ else [])

        # Regex for message patterns that cause user ban
        self.message_ban_patterns = os.environ['MESSAGE_BAN_PATTERNS']
        self.message_ban_re = (re.compile(
            self.message_ban_patterns,
            re.IGNORECASE | re.VERBOSE)
            if self.message_ban_patterns else None)

        # Regex for message patterns that cause message to be hidden
        self.message_hide_patterns = os.environ['MESSAGE_HIDE_PATTERNS']
        self.message_hide_re = (re.compile(
            self.message_hide_patterns,
            re.IGNORECASE | re.VERBOSE)
            if self.message_hide_patterns else None)

        # Regex for name patterns that cause user to be banned
        self.name_ban_patterns = os.environ['NAME_BAN_PATTERNS']
        self.name_ban_re = (re.compile(
            self.name_ban_patterns,
            re.IGNORECASE | re.VERBOSE)
            if self.name_ban_patterns else None)


    @MWT(timeout=60*60)
    def get_admin_ids(self, bot, chat_id):
        """ Returns a list of admin IDs for a given chat. Results are cached for 1 hour. """
        return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


    def ban_user(self, update):
        """ Ban user """
        kick_success = update.message.chat.kick_member(update.message.from_user.id)


    def security_check_username(self, bot, update):
        """ Test username for security violations """

        full_name = (update.message.from_user.first_name + " "
            + update.message.from_user.last_name)
        if self.name_ban_re and self.name_ban_re.search(full_name):
            # Logging
            log_message = "❌ 🙅‍♂️ BAN MATCH FULL NAME: {}".format(full_name.encode('utf-8'))
            if self.debug:
                update.message.reply_text(log_message)
            print(log_message)
            # Ban the user
            self.ban_user(update)
            # Log in database
            s = session()
            userBan = UserBan(
                user_id=update.message.from_user.id,
                reason=log_message)
            s.add(userBan)
            s.commit()
            s.close()
            # Notify channel
            bot.sendMessage(chat_id=self.notify_chat, text=log_message)

        if self.name_ban_re and self.name_ban_re.search(update.message.from_user.username or ''):
            # Logging
            log_message = "❌ 🙅‍♂️ BAN MATCH USERNAME: {}".format(update.message.from_user.username.encode('utf-8'))
            if self.debug:
                update.message.reply_text(log_message)
            print(log_message)
            # Ban the user
            self.ban_user(update)
            # Log in database
            s = session()
            userBan = UserBan(
                user_id=update.message.from_user.id,
                reason=log_message)
            s.add(userBan)
            s.commit()
            s.close()
            # Notify channel
            bot.sendMessage(chat_id=self.notify_chat, text=log_message)


    def security_check_message(self, bot, update):
        """ Test message for security violations """

        if not update.message.text:
            return

        # Remove accents from letters (é->e, ñ->n, etc...)
        message = unidecode.unidecode(update.message.text)
        # TODO: Replace lookalike unicode characters:
        # https://github.com/wanderingstan/Confusables

        # Hide forwarded messages
        if update.message.forward_date is not None:
            # Logging
            log_message = "❌ HIDE FORWARDED: {}".format(update.message.text.encode('utf-8'))
            if self.debug:
                update.message.reply_text(log_message)
            print(log_message)
            # Delete the message
            update.message.delete()
            # Log in database
            s = session()
            messageHide = MessageHide(
                user_id=update.message.from_user.id,
                message=update.message.text)
            s.add(messageHide)
            s.commit()
            s.close()
            # Notify channel
            bot.sendMessage(chat_id=self.notify_chat, text=log_message)

        if self.message_ban_re and self.message_ban_re.search(message):
            # Logging
            log_message = "❌ 🙅‍♂️ BAN MATCH: {}".format(update.message.text.encode('utf-8'))
            if self.debug:
                update.message.reply_text(log_message)
            print(log_message)
            # Any message that causes a ban gets deleted
            update.message.delete()
            # Ban the user
            self.ban_user(update)
            # Log in database
            s = session()
            userBan = UserBan(
                user_id=update.message.from_user.id,
                reason=update.message.text)
            s.add(userBan)
            s.commit()
            s.close()
            # Notify channel
            bot.sendMessage(chat_id=self.notify_chat, text=log_message)

        elif self.message_hide_re and self.message_hide_re.search(message):
            # Logging
            log_message = "❌ 🙈 HIDE MATCH: {}".format(update.message.text.encode('utf-8'))
            if self.debug:
                update.message.reply_text(log_message)
            print(log_message)
            # Delete the message
            update.message.delete()
            # Log in database
            s = session()
            messageHide = MessageHide(
                user_id=update.message.from_user.id,
                message=update.message.text)
            s.add(messageHide)
            s.commit()
            s.close()
            # Notify channel
            bot.sendMessage(chat_id=self.notify_chat, text=log_message)


    def attachment_check(self, bot, update):
        """ Hide messages with attachments (except photo or video) """
        if (update.message.audio or
            update.message.document or
            update.message.game or
            update.message.voice):
            # Logging
            if update.message.document:
                log_message = "❌ HIDE DOCUMENT: {}".format(update.message.document.__dict__)
            else:
                log_message = "❌ HIDE NON-DOCUMENT ATTACHMENT"
            if self.debug:
                update.message.reply_text(log_message)
            print(log_message)
            # Delete the message
            update.message.delete()
            # Log in database
            s = session()
            messageHide = MessageHide(
                user_id=update.message.from_user.id,
                message=update.message.text)
            s.add(messageHide)
            s.commit()
            s.close()
            # Notify channel
            bot.sendMessage(chat_id=self.notify_chat, text=log_message)


    def logger(self, bot, update):
        """ Primary Logger. Handles incoming bot messages and saves them to DB """
        try:
            user = update.message.from_user

            # Limit bot to monitoring certain chats
            if update.message.chat_id not in self.chat_ids:
                print("Message from user {} is from chat_id not being monitored: {}".format(
                    user.id,
                    update.message.chat_id)
                )
                return

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
            else:
                print("{} {} ({}) : non-message".format(
                    strftime("%Y-%m-%dT%H:%M:%S"),
                    user.id,
                    (user.username or (user.first_name + " " + user.last_name) or "").encode('utf-8'))
                )

            # Don't check admin activity
            is_admin = update.message.from_user.id not in self.get_admin_ids(bot, update.message.chat_id)
            if is_admin and self.admin_exempt:
                print("👮‍♂️ Skipping checks. User is admin: {}".format(user.id))
            else:
                # Security checks
                self.attachment_check(bot, update)
                self.security_check_username(bot, update)
                self.security_check_message(bot, update)

        except Exception as e:
            print("Error: {}".format(e))
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

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
            print("Error: {}".format(e))


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
            return self.id_exists(user_id)
        except Exception as e:
            print("Error: {}".format(e))


    def error(self, bot, update, error):
        """ Log Errors caused by Updates. """
        print("Update '{}' caused error '{}'".format(update, error),
            file=sys.stderr)


    def start(self):
        """ Start the bot. """

        # Create the EventHandler and pass it your bot's token.
        updater = Updater(os.environ["TELEGRAM_BOT_TOKEN"])

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(
            Filters.all,
            lambda bot, update : self.logger(bot, update)
        ))

        # dp.add_handler(MessageHandler(Filters.status_update, status))

        # log all errors
        dp.add_error_handler(
            lambda bot, update, error : self.error(bot, update, error)
        )

        # Start the Bot
        updater.start_polling()

        print("Bot started. Montitoring chats: {}".format(self.chat_ids))

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


if __name__ == '__main__':
    c = TelegramMonitorBot()

    c.start()
