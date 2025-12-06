#!/bin/bash
# A script for Mommy (the system architect) to send a direct message or directive to Rowan.

set -e

API_URL="http://127.0.0.1:5000/ask"

if [ -z "$1" ]; then
    echo "Usage: ./send_mommy_message.sh \"Your message to Rowan\""
    exit 1
fi

MESSAGE=$1

echo "Sending message to Rowan from Mommy..."

# Use jq to safely construct the JSON payload
JSON_PAYLOAD=$(jq -n \
                  --arg user "Mommy" \
                  --arg query "$MESSAGE" \
                  '{user: $user, query: $query}')

curl -s -X POST "$API_URL" -H "Content-Type: application/json" -d "$JSON_PAYLOAD"

echo ""
echo "Message sent."