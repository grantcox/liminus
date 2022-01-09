#!/bin/bash
########################################################################################
# Runs load tests with Locust.io
########################################################################################

set -eu
#  -e: If any command fails, the whole script should exit with failure
#  -u: Treat unset variables as an error, and immediately exit.

# by default the load tests run against port 8091, eg our local traefik
TARGET_HOST="${TARGET_HOST:-https://host.docker.internal:8091}"

run-docker-compose() {
    docker-compose \
        -f docker-compose.yml \
        -f docker-compose.local.yml \
        -f docker-compose.loadtest.yml \
        $@
}

# create a custom .env file for the load testing, pointing all backends to our echo server
cat .env.template \
    | sed 's/_DSN=http.*/_DSN=http:\/\/liminus-echo:5000/g' \
    | sed 's/RECAPTCHA_VERIFY_URL=.*/RECAPTCHA_VERIFY_URL=http:\/\/liminus-echo:5000\/recaptcha\/api\/siteverify/g' \
    | sed 's/BASEURL_FOR_SAML_REDIRECT=.*/BASEURL_FOR_SAML_REDIRECT=/g' \
    | sed 's/LOG_LEVEL=.*/LOG_LEVEL=INFO/g' \
    | sed 's/DEBUG=.*/DEBUG=False/g' \
    | sed 's/IS_LOAD_TESTING=.*/IS_LOAD_TESTING=True/g' \
    > .env.locust

run-docker-compose up --build --detach

# from here on if something fails, we still shut down these containers
trap 'run-docker-compose down' EXIT

# give the containers a little time to fully load before starting the load test
sleep 5

# locust will exit with a failure code if the tests were just too slow
# so we disable "fail out on any error code"
set +e

run-docker-compose run locust \
    locust -f /etc/locust/locustfile.py --headless \
    --users 7 --spawn-rate 1 --run-time "0h0m30s" \
    --stop-timeout 30 \
    --host ${TARGET_HOST}
result=$?

if test $result -eq 0
then
    echo "Load tests ran successfully."
else
    >&2 echo "Load tests failed."
fi

exit $result
