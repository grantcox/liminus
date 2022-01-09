#!/bin/bash

# this script is used to 100% ensure we're running the latest app code
# sometimes it's helpful to be sure of that!
set -e

SERVICE_NAME=app

./scripts/docker-compose-local.sh build $SERVICE_NAME
./scripts/docker-compose-local.sh stop --timeout 0 $SERVICE_NAME
./scripts/docker-compose-local.sh rm -f -v $SERVICE_NAME
./scripts/docker-compose-local.sh up -d $SERVICE_NAME
