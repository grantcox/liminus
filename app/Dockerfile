FROM python:3.9-slim-buster
RUN pip install --upgrade pipenv

WORKDIR /usr/app/

# install service dependencies
COPY Pipfile* ./

# when BUILD_DEV is empty (default), we do not install dev dependencies with pipenv
# when it has a value (eg BUILD_DEV=1 in the docker-compose), we do install dev deps
ARG BUILD_DEV
ENV PIPENV_DEV_FLAG=${BUILD_DEV:+"--dev"}
RUN pipenv install ${PIPENV_DEV_FLAG} --system --deploy --ignore-pipfile --sequential --verbose

EXPOSE 5000

# copy the app code
COPY . .
