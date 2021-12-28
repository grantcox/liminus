#!/bin/bash

set -e

SERVICE_NAME=app

./scripts/docker-compose-local.sh build $SERVICE_NAME
./scripts/docker-compose-local.sh stop --timeout 0 $SERVICE_NAME
./scripts/docker-compose-local.sh rm -f -v $SERVICE_NAME
./scripts/docker-compose-local.sh up -d $SERVICE_NAME
