#!/bin/bash
########################################################################################
# Start the docker containers in a detached state for local development
########################################################################################

set -e

./scripts/docker-compose-local.sh up --build --detach $@
