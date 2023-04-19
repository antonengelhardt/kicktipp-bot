#!/bin/bash

echo -n "Do you want to save your input to your .bash_profile or .zshrc or none (just for this session)? (bash/zsh/none)"
read SAVE_TO_PROFILE

echo -n "Please enter the following details"

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

# save to .bash_profile, .zshrc or none

if [ $SAVE_TO_PROFILE == "bash"]
then
    $KICKTIPP_EMAIL >> ~/.bash_profile
    $KICKTIPP_PASSWORD >> ~/.bash_profile
    $KICKTIPP_NAME_OF_COMPETITION >> ~/.bash_profile
    $ZAPIER_URL >> ~/.bash_profile
    echo -n "Saved to .bash_profile"
elif [ $SAVE_TO_PROFILE == "zsh"]
then
    $KICKTIPP_EMAIL >> ~/.zshrc
    $KICKTIPP_PASSWORD >> ~/.zshrc
    $KICKTIPP_NAME_OF_COMPETITION >> ~/.zshrc
    $ZAPIER_URL >> ~/.zshrc
    echo -n "Saved to .zshrc"
else
    echo -n "Not saving to .bash_profile or .zshrc"
fi
