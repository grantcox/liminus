#!/bin/bash
########################################################################################
# Configure local environment
########################################################################################

set -e


# configure hostname
HOST_TO_ADD='127.0.0.1 localhost local.liminus'
if [ -n "$(grep "$HOST_TO_ADD" /etc/hosts)" ]
then
    echo "host already added"
else
    echo "Adding entry to /etc/hosts. You may be prompted for your machine's password."
    sudo bash -c "echo $HOST_TO_ADD >> /etc/hosts"
fi

# create and fill .env
if [[ ! -f .env ]]
then
    cp .env.template .env
fi

# set up pre-commit hooks
if ! command -v pre-commit &> /dev/null
then
    echo "installing pre-commit package"
    brew install pre-commit
fi
echo "installing pre-commit hook"
pre-commit install
