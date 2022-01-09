#!/bin/bash
set -u
#  -u: Treat unset variables as an error, and immediately exit.

# ensure the dev app container is running
scripts/docker-compose-local.sh up --build --detach app
scripts/docker-compose-local.sh exec app pytest $@
testsExitCode=$?

if [[ $testsExitCode -eq 0 ]]
then
    echo "All tests passed!!! 🥳"
else
    echo "Integration tests failed! 👻"
fi

exit $testsExitCode
