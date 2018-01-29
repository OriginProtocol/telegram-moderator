# Telegram Group Chat Logger

This is a bot that logs public Group Chats to a Postgres Database.

## Installation

 - Required: Python 3.x, pip, PostgreSQL
 - Clone this repo
 - `pip install --upgrade -r requirements.txt`

## Telegram Bot Setup

 - Create a bot by talking to BotFather: https://core.telegram.org/bots#creating-a-new-bot
 - Store your Telegram Bot Token in environment variable `BOT_TOKEN`. It will look similar to this:
 ```
 export TELEGRAM_BOT_TOKEN="4813829027:ADJFKAf0plousH2EZ2jBfxxRWFld3oK34ya"
 ```
 - Create a Telegram group.
 - Add your bot to the group like so: https://stackoverflow.com/questions/37338101/how-to-add-a-bot-to-a-telegram-group
 - Use `/setprivacy` with `@BotFather` in order to allow it to see all messages in a group.

## Running the bot

 - Create a Postgres database.
 ```
 $psql
CREATE DATABASE telegram_bot_db;
```
 - Copy `config.cnf.sample` to `config.cnf` and edit the databse connection URL. File should look like this:
 ```
[postgres]
postgres_url = postgresql://<user>:<password>@localhost:5432/<databasename>
```
 - Run: `python model.py` to setup the DB tables.
 - Run: `python bot.py` to start logger
 - When a messages is successfully logged, `message logged` will be displayed.
