#!/bin/bash

echo
echo "Please enter the following details"

echo -n "Kicktipp Email: "
read KICKTIPP_EMAIL

echo -n "Kicktipp Password: "
read KICKTIPP_PASSWORD

echo -n "Kicktipp Name of Competition: "
read KICKTIPP_NAME_OF_COMPETITION

echo -n "How many hours before the game should the games be tipped? (default 2): "
read KICKTIPP_HOURS_UNTIL_GAME

echo -n "Zapier Url (press enter to skip): "
read ZAPIER_URL

echo "export KICKTIPP_EMAIL=$KICKTIPP_EMAIL" >> .env
echo "export KICKTIPP_PASSWORD=$KICKTIPP_PASSWORD" >> .env
echo "export KICKTIPP_NAME_OF_COMPETITION=$KICKTIPP_NAME_OF_COMPETITION" >> .env
echo "export KICKTIPP_HOURS_UNTIL_GAME=$KICKTIPP_HOURS_UNTIL_GAME " >> .env
if [ -z "$ZAPIER_URL" ]; then
    echo "Zapier Url not set"
else
    echo "export ZAPIER_URL=$ZAPIER_URL" >> .env
    echo "Zapier Url set"
fi
