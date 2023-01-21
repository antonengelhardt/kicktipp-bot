#!/bin/bash

echo
echo "Please enter the following details"

echo -n "Kicktipp Email: "
read KICKTIPP_EMAIL

echo -n "Kicktipp Password: "
read KICKTIPP_PASSWORD

echo -n "Kicktipp Name of Competition: "
read KICKTIPP_NAME_OF_COMPETITION

echo -n "Zapier Url: "
read ZAPIER_URL

export KICKTIPP_EMAIL=$KICKTIPP_EMAIL
export KICKTIPP_PASSWORD=$KICKTIPP_PASSWORD
export KICKTIPP_NAME_OF_COMPETITION=$KICKTIPP_NAME_OF_COMPETITION
export ZAPIER_URL=$ZAPIER_URL