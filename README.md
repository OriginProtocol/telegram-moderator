# Telegram Bot

- Deletes messages matching specified patterns
- Bans users for posting messagses matching specified patterns
- Bans users with usernames matching specified patterns
- Records logs of converstations

## Installation

 - Required: Python 3.x, pip, PostgreSQL
 - Create virtualenv
 - Clone this repo
 - `pip install --upgrade -r requirements.txt`

## Database setup
 - Store database URL in environment variable.
 ```
 export TELEGRAM_BOT_POSTGRES_URL="postgresql://<user>:<password>@localhost:5432/<databasename>"
 ```
 - Run: `python model.py` to setup the DB tables.

## Setup

 - Create a Telegram bot by talking to `@BotFather` : https://core.telegram.org/bots#creating-a-new-bot
 - Use `/setprivacy` with `@BotFather` in order to allow it to see all messages in a group.
 - Store your Telegram Bot Token in environment variable `TELEGRAM_BOT_TOKEN`. It will look similar to this:

 ```
 export TELEGRAM_BOT_TOKEN="4813829027:ADJFKAf0plousH2EZ2jBfxxRWFld3oK34ya"
 ```
 - Create your Telegram group.
 - Add your bot to the group like so: https://stackoverflow.com/questions/37338101/how-to-add-a-bot-to-a-telegram-group
 - Make your bot an admin in the group

## Configuring patterns

- Regex patterns will be read from the following env variables
	- `MESSAGE_BAN_PATTERNS` Messages matching this will ban the user.
	- `MESSAGE_HIDE_PATTERNS` Messages matching this will be hidden/deleted
	- `NAME_BAN_PATTERNS` Users with usernames or first/last names maching this will be banned from the group.
	- `SAFE_USER_IDS` User ID's that are except from these checkes. Note that the bot cannot ban admin users, but can delete their messages.

Sample bash file to set `MESSAGE_BAN_PATTERNS`:
```
read -r -d '' MESSAGE_BAN_PATTERNS << 'EOF'
# ETH
# e.g. F8C8405e85Cfe42551DEfeB2a4548A33bb3DF840
[0-9a-fA-F]{40,40}
# BTC 13qt9rCA2CQLZedmUuDiPkwdcAJLsuTvLm
# e.g.
|[0-9a-fA-Z]{34,34}
EOF
```

## Running the bot
 - Run: `python bot.py` to start.
 - Messages will be displayed on `stdout` as they are logged.

