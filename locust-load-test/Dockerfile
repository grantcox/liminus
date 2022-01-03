FROM python:3.9-slim-buster

WORKDIR /usr/app/

# install service dependencies
COPY * ./

RUN pipenv install --system --deploy --ignore-pipfile --sequential --verbose

EXPOSE 5000

CMD [ "gunicorn", "echo:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000" ]

