#!/bin/bash
########################################################################################
# Runs load tests with Locust.io
########################################################################################

set -ex

DOCKER_REGISTRY="912617429107.dkr.ecr.us-west-2.amazonaws.com"

if [[ -z $PROJECT ]]; then
    PROJECT="liminus-local"
fi

cat .env.template \
    | sed 's/_DSN=http.*/_DSN=http:\/\/liminus-echo:5000/g' \
    | sed 's/BASEURL_FOR_SAML_REDIRECT=.*/BASEURL_FOR_SAML_REDIRECT=/g' \
    | sed 's/LOG_LEVEL=.*/LOG_LEVEL=INFO/g' \
    | sed 's/DEBUG=.*/DEBUG=False/g' \
    > locust-load-test/.env

PROJECT="liminus-local" docker-compose \
    -f docker-compose.yml \
    -f docker-compose.local.yml \
    -f docker-compose.loadtest.yml \
    down

# we always rebuild the docker containers as we assume some code has changed since last time
PROJECT=$PROJECT docker-compose \
    -f docker-compose.yml \
    -f docker-compose.local.yml \
    -f docker-compose.loadtest.yml \
    --project-name "$PROJECT" \
    up --detach --build

# PROJECT=$PROJECT docker-compose \
#     -f docker-compose.yml \
#     -f docker-compose.local.yml \
#     -f docker-compose.loadtest.yml \
#     --project-name "$PROJECT" \
#     logs --follow --tail 100
# exit 0

sleep 5

if [[ -z $TARGET_HOST ]]; then
    TARGET_HOST=https://host.docker.internal:8091
fi

IMAGE_NAME="$DOCKER_REGISTRY/avaaz/locust"
RUN_TIME="0h0m30s"

echo "Running load tests against host $TARGET_HOST for $RUN_TIME"
docker run \
    --env PYTHONDONTWRITEBYTECODE=1 \
    --name="$CONTAINER_NAME" \
    -v "$PWD/locust-load-test/:/etc/locust/" \
    --rm \
    $IMAGE_NAME -f /etc/locust/locustfile.py --headless -u 1 -r 10 --run-time "$RUN_TIME" --stop-timeout 30 -H ${TARGET_HOST}

result=$?

if test $result -eq 0
then
 echo "Load tests ran successfully."
else
 >&2 echo "Load tests failed."
fi

PROJECT=$PROJECT docker-compose \
    -f docker-compose.yml \
    -f docker-compose.local.yml \
    -f docker-compose.loadtest.yml \
    --project-name "$PROJECT" \
    logs --follow --tail 100

docker-compose \
    -f docker-compose.yml \
    -f docker-compose.local.yml \
    -f docker-compose.loadtest.yml \
    down

exit $result