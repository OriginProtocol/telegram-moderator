![origin_github_banner](https://user-images.githubusercontent.com/673455/37314301-f8db9a90-2618-11e8-8fee-b44f38febf38.png)
 
Head to https://www.originprotocol.com/developers to learn more about what we're building and how to get involved.

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

## Configuration with ENV vars

- `MESSAGE_BAN_PATTERNS` : **REQUIRED** Regex pattern. Messages matching this will ban the user.
- `MESSAGE_HIDE_PATTERNS` : **REQUIRED** Regex pattern. Messages matching this will be hidden/deleted
- `NAME_BAN_PATTERNS` **REQUIRED** Regex pattern. Users with usernames or first/last names maching this will be banned from the group.
- `CHAT_IDS` : **REQUIRED**. Comma-seperated list of IDs of chat(s) that should be monitored. To find out the ID of a chat, add the bot to a chat and type some messages there. The bot log will report an error that it got messages `from chat_id not being monitored: XXX` where XXX is the chat ID. e.g. `-240532994,-150531679`
- `TELEGRAM_BOT_TOKEN` : **REQUIRED**. Token for bot to control. e.g. `4813829027:ADJFKAf0plousH2EZ2jBfxxRWFld3oK34ya`
- `TELEGRAM_BOT_POSTGRES_URL` : **REQUIRED**. URI for postgres instance to log activity to. e.g. `postgresql://localhost/postgres`
- `DEBUG` : If set to anything except `false`, will put bot into debug mode. This means that all actions will be logged into the chat itself, and more things will be logged. 
- `ADMIN_EXEMPT` : If set to anything except `false`, admin users will be exempt from monitoring. Reccomended to be set, but useful to turn off for debugging. 
- `NOTIFY_CHAT` : ID of chat to report actions. Can be useful if you have an admin-only chat where you want to monitor the bot's activity. E.g. `-140532994`

Sample bash file to set `MESSAGE_BAN_PATTERNS`:
```
read -r -d '' MESSAGE_BAN_PATTERNS << 'EOF'
# ETH Address
# e.g. F8C8405e85Cfe42551DEfeB2a4548A33bb3DF840
[0-9a-fA-F]{40,40}
# BTC Address
# e.g. 13qt9rCA2CQLZedmUuDiPkwdcAJLsuTvLm
|[0-9a-fA-Z]{34,34}
EOF
```

## Attachements

By default, any attachments other than images or animations will cause the message to be hidden. 

## Running

### Locally
 - Run: `python bot.py` to start logger
 - Messages will be displayed on `stdout` as they are logged.

### On Heroku
 - You must enable the worker on Heroku app dashboard. (By default it is off.)
