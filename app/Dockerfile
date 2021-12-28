FROM python:3.9-slim-buster
RUN pip install --upgrade pipenv

WORKDIR /usr/app/

# RUN echo "Installing pip package 'cryptography' build dependencies as per https://cryptography.io/en/latest/installation/" && \
#     apt-get install -y build-essential libssl-dev libffi-dev python3-dev cargo

# install service dependencies
COPY Pipfile* ./

# when BUILD_DEV is empty (default), we do not install dev dependencies with pipenv
# when it has a value (eg BUILD_DEV=1 in the docker-compose), we do install dev deps
ARG BUILD_DEV
ENV PIPENV_DEV_FLAG=${BUILD_DEV:+"--dev"}
RUN pipenv install ${PIPENV_DEV_FLAG} --system --deploy --ignore-pipfile --sequential --verbose

# RUN echo "Removing 'cryptography' build dependencies" && \
#     apt-get remove -y build-essential libssl-dev libffi-dev python3-dev cargo

EXPOSE 5000

# copy the app code
COPY . .
