# -*- coding: utf-8 -*-

"""Group Chat Logger

This bot is a modified version of the echo2 bot found here:
https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py

This bot logs all messages sent in a Telegram Group to a database.

"""

#from __future__ import print_function
import os
import sys
import re
import unidecode
import locale
from time import strftime
from datetime import datetime, timedelta

import requests
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from model import User, Message, MessageHide, UserBan, session
from mwt import MWT
from googletrans import Translator
from textblob import TextBlob

# Used with monetary formatting
locale.setlocale(locale.LC_ALL, '')

# Price data cache duration
CACHE_DURATION = timedelta(minutes=15)

# CMC IDs can be retrived at:
# https://pro-api.coinmarketcap.com/v1/cryptocurrency/map?symbol=[SYMBOL]
CMC_SYMBOL_TO_ID = {
    'OGN': 5117,
    'USDT': 825,
    'USDC': 3408,
    'DAI': 4943,
}
CMC_API_KEY = os.environ.get('CMC_API_KEY')
CMC_QUOTE_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?id={}'


def first_of(attr, match, it):
    """ Return the first item in a set with an attribute that matches match """
    if it is not None:
        for i in it:
            try:
                if getattr(i, attr) == match:
                    return i
            except: pass

    return None


def command_from_message(message, default=None):
    """ Extracts the first command from a Telegram Message """
    if not message or not message.text:
        return default

    command = None
    text = message.text
    entities = message.entities
    command_def = first_of('type', 'bot_command', entities)

    if command_def:
        command = text[command_def.offset:command_def.length]

    return command or default


def cmc_get_data(jso, cmc_id, pair_symbol='USD'):
    """ Pull relevant data from a response object """
    if not jso:
        return None

    data = jso.get('data', {})
    specific_data = data.get(str(cmc_id), {})
    quote = specific_data.get('quote', {})
    symbol_data = quote.get(pair_symbol, {})
    return {
        'price': symbol_data.get('price'),
        'volume': symbol_data.get('volume_24h'),
        'percent_change': symbol_data.get('percent_change_24h'),
        'market_cap': symbol_data.get('market_cap'),
    }


def monetary_format(v, decimals=2):
    if not v:
        v = 0
    f = locale.format('%.{}f'.format(decimals), v, grouping=True)
    return '${}'.format(f)


class TokenData:
    def __init__(self, symbol, price=None, stamp=datetime.now()):
        self.symbol = symbol
        self._price = price
        self._percent_change = 0
        self._volume = 0
        self._market_cap = 0
        if price is not None:
            self.stamp = stamp
        else:
            self.stamp = None

    def _fetch_from_cmc(self):
        """ Get quote data for a specific known symbol """
        jso = None

        cmc_id = CMC_SYMBOL_TO_ID.get(self.symbol)
        url = CMC_QUOTE_URL.format(cmc_id)
        r = requests.get(url, headers={
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json',
        })
        if r.status_code != 200:
            print('Failed to fetch price data for id: {}'.format(cmc_id))
            return None
        try:
            jso = r.json()
        except Exception:
            print('Error parsing JSON')
            return None
        return jso

    def update(self):
        """ Fetch price from binance """
        if self.stamp is None or (
            self.stamp is not None
            and self.stamp < datetime.now() - CACHE_DURATION
        ):
            # CMC
            jso = self._fetch_from_cmc()
            data = cmc_get_data(jso, CMC_SYMBOL_TO_ID[self.symbol])
            if data is not None:
                self._price = data.get('price')
                self._percent_change = data.get('percent_change')
                self._volume = data.get('volume')
                self._market_cap = data.get('market_cap')
                self.stamp = datetime.now()

    @property
    def price(self):
        self.update()
        return self._price

    @property
    def volume(self):
        self.update()
        return self._volume

    @property
    def percent_change(self):
        self.update()
        pc = str(self._percent_change)
        if pc and not pc.startswith('-'):
            pc = '+{}'.format(pc)
        return pc

    @property
    def market_cap(self):
        self.update()
        return self._market_cap


class TelegramMonitorBot:


    def __init__(self):
        self.debug = (
            (os.environ.get('DEBUG') is not None) and
            (os.environ.get('DEBUG').lower() != "false"))

        # Are admins exempt from having messages checked?
        self.admin_exempt = (
            (os.environ.get('ADMIN_EXEMPT') is not None) and
            (os.environ.get('ADMIN_EXEMPT').lower() != "false"))

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

        # Mime type document check
        # NOTE: All gifs appear to be converted to video/mp4
        mime_types = os.environ.get('ALLOWED_MIME_TYPES', 'video/mp4')
        self.allowed_mime_types = set(map(lambda s: s.strip(), mime_types.split(',')))

        # Comamnds
        self.available_commands = ['flip', 'unflip']
        if CMC_API_KEY is not None:
            self.available_commands.append('price')

        # Cached token prices
        self.cached_prices = {}


    @MWT(timeout=60*60)
    def get_admin_ids(self, bot, chat_id):
        """ Returns a list of admin IDs for a given chat. Results are cached for 1 hour. """
        return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


    def ban_user(self, update):
        """ Ban user """
        kick_success = update.message.chat.kick_member(update.message.from_user.id)


    def security_check_username(self, bot, update):
        """ Test username for security violations """

        full_name = "{} {}".format(
            update.message.from_user.first_name,
            update.message.from_user.last_name)
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
                # GIFs are documents and allowed
                mime_type = update.message.document.mime_type
                if mime_type and mime_type in self.allowed_mime_types:
                    return
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
                self.log_message(user.id, update.message.text,
                                 update.message.chat_id)
            else:
                add_user_success = self.add_user(
                    user.id,
                    user.first_name,
                    user.last_name,
                    user.username)

                if add_user_success:
                    self.log_message(
                        user.id, update.message.text, update.message.chat_id)
                    print("User added: {}".format(user.id))
                else:
                    print("Something went wrong adding the user {}".format(user.id), file=sys.stderr)

            user_name = (
                user.username or
                "{} {}".format(user.first_name, user.last_name) or
                "<none>").encode('utf-8')
            if update.message.text:
                print("{} {} ({}) : {}".format(
                    strftime("%Y-%m-%dT%H:%M:%S"),
                    user.id,
                    user_name,
                    update.message.text.encode('utf-8'))
                )
            else:
                print("{} {} ({}) : non-message".format(
                    strftime("%Y-%m-%dT%H:%M:%S"),
                    user.id,
                    user_name)
                )

            # Don't check admin activity
            is_admin = update.message.from_user.id in self.get_admin_ids(bot, update.message.chat_id)
            if is_admin and self.admin_exempt:
                print("👮‍♂️ Skipping checks. User is admin: {}".format(user.id))
            else:
                # Security checks
                self.attachment_check(bot, update)
                self.security_check_username(bot, update)
                self.security_check_message(bot, update)

        except Exception as e:
            print("Error[292]: {}".format(e))
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

    def log_message(self, user_id, user_message, chat_id):

        if user_message is None:
            user_message = "[NO MESSAGE]"

        try:
            s = session()
            language_code = english_message = ""
            polarity = subjectivity = 0.0
            try:
                # translate to English & log the original language
                translator = Translator()
                translated = translator.translate(user_message)
                language_code = translated.src
                english_message = translated.text
                # run basic sentiment analysis on the translated English string
                analysis = TextBlob(english_message)
                polarity = analysis.sentiment.polarity
                subjectivity = analysis.sentiment.subjectivity
            except Exception as e:
                print(str(e))
            msg1 = Message(user_id=user_id, message=user_message, chat_id=chat_id, 
                language_code=language_code, english_message=english_message, polarity=polarity,
                subjectivity=subjectivity)
            s.add(msg1)
            s.commit()
            s.close()
        except Exception as e:
            print("Error logging message: {}".format(e))


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
            print("Error[347]: {}".format(e))

    def handle_command(self, bot, update):
        """ Handles commands

        Note: Args reversed from docs?  Maybe version differences?  Docs say
        cb(update, context) but we're getting cb(bot, update).

        update: Update: https://python-telegram-bot.readthedocs.io/en/stable/telegram.update.html#telegram.Update
        context: CallbackContext: https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.callbackcontext.html

        hi: says hi
        price: prints the OGN price
        """
        chat_id = None
        command = None

        command = command_from_message(update.effective_message)

        if update.effective_message.chat:
            chat_id = update.effective_message.chat.id

        print('command: {} seen in chat_id {}'.format(command, chat_id))

        if command == '/hi':
            bot.send_message(chat_id, 'Yo whattup, @{}!'.format(update.effective_user.username))

        elif command == '/flip':
            bot.send_message(chat_id, '╯°□°）╯︵ ┻━┻')

        elif command == '/unflip':
            bot.send_message(chat_id, '┬──┬﻿ ¯\\_(՞▃՞ ¯\\_)')

        elif command == '/price':
            """ Price, 24 hour %, 24 hour volume, and market cap """
            symbol = 'OGN'
            if symbol not in self.cached_prices:
                self.cached_prices[symbol] = TokenData(symbol)
            pdata = self.cached_prices[symbol]
            message = """
*Origin Token* (OGN)
*Price*: {} ({}%)
*Market Cap*: {}
*Volume(24h)*: {}

@{}""".format(
                monetary_format(pdata.price, decimals=5),
                pdata.percent_change,
                monetary_format(pdata.market_cap),
                monetary_format(pdata.volume),
                update.effective_user.username,
            )
            bot.send_message(chat_id, message, parse_mode=telegram.ParseMode.MARKDOWN)


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

        # on commands
        dp.add_handler(
            CommandHandler(
                command=self.available_commands,
                callback=self.handle_command,
                filters=Filters.all,
            )
        )

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
