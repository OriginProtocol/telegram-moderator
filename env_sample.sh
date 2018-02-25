# Example env vars for bot

export TELEGRAM_BOT_POSTGRES_URL="postgresql://postgres:postgres@localhost/origindb"

read -r -d '' MESSAGE_BAN_PATTERNS << 'EOF'
# ETH
# e.g. F8C8405e85Cfe42551DEfeB2a4548A33bb3DF840
[0-9a-fA-F]{40,40}
# BTC
# e.g. 13qt9rCA2CQLZedmUuDiPkwdcAJLsuTvLm
|[0-9a-zA-Z]{34,34}
EOF

read -r -d '' MESSAGE_HIDE_PATTERNS << 'EOF'
# ETH
# e.g. F8C8405e85Cfe42551DEfeB2a4548A33bb3DF840
|[0-9a-fA-F]{40,40}
# BTC
# e.g. 13qt9rCA2CQLZedmUuDiPkwdcAJLsuTvLm
|[0-9a-zA-Z]{34,34}
EOF

export TELEGRAM_BOT_TOKEN="XXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

export NAME_BAN_PATTERNS="admin$"

export CHAT_IDS="-250531994"
