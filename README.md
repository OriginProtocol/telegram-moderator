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

## Database setup
 - Store database URL in environment variable.
 ```
 export TELEGRAM_BOT_POSTGRES_URL="postgresql://<user>:<password>@localhost:5432/<databasename>"
 ```
 - Run: `python model.py` to setup the DB tables.

## Running the bot
 - Run: `python bot.py` to start logger
 - Messages will be displayed on `stdout` as they are logged.
