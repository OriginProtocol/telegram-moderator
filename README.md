# Telegram Group Chat Logger

This is a bot that logs public Group Chats to an SQL Database.

## Installation

 - Required: Python 3.X , PostgreSQL, Telegram Bot
 - Clone this repo
 - `pip install requirements.txt`
 
## Bot/Group Setup

 - Create a group
 - Add your bot to the group like so: https://stackoverflow.com/questions/37338101/how-to-add-a-bot-to-a-telegram-group
 - your bot only sees commands. Use `/setprivacy` with `@BotFather` in order to allow it to see all messages in a group.
 
## Running the bot

 - Create a Database, eg. `origindb`
 - Store your Telegram Bot Token in an environment variable, eg. `echo $ORIGINTOKEN`
 - Add your DB credentials to `model.py` eg. `engine = create_engine('postgresql://postgres:<password>@localhost:5432/<databasename>')`
 - Run: `python model.py` to setup the DB tables, etc.
 - Run: `python bot.py` to start logger