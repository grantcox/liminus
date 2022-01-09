#!/bin/bash

# if this script is run with the --apply arg, then black and isort will attempt to fix issues
# without that (default) they just print warning and exit with an error code

if [[ "$1" == "--apply" ]];then
    blackArgs=""
    isortArgs=""

else
    blackArgs="--check"
    isortArgs="--check --diff"
fi

# ensure the dev app container is running
scripts/docker-compose-local.sh up --build --detach app

run-in-app() {
    scripts/docker-compose-local.sh exec app $@
}

echo "Running black..."
run-in-app black $blackArgs --config=pyproject.toml .
resultBlack=$?

echo "Running isort..."
run-in-app isort --settings-path=setup.cfg . $isortArgs
resultIsort=$?

echo "Running flake8..."
run-in-app flake8 --config=setup.cfg
resultFlake=$?

echo "Running mypy..."
run-in-app mypy --config-file=setup.cfg .
resultMypy=$?

if [[ $resultFlake -ne 0 || $resultBlack -ne 0 || $resultIsort -ne 0 || $resultMypy -ne 0 ]];then
    SCRIPT_NAME=$(basename "$0")
    echo "Static analysis failed! 👻 "
    echo "For black/isort, simply run '$SCRIPT_NAME --apply'"
    exit 1
fi

echo "Static analysis succeeded! 🥳"

