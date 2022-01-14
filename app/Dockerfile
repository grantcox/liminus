# in local dev and static analysis environments we want dev dependencies installed,
# but in load testing and deploy envs we only want prod dependencies
# this is handled by having two named stages ("prod" and "dev")
# this means any build will create both stages, and we use the runtime BUILD_DEV
# arg to determine which stage is actually executed
ARG BUILD_DEV=0
ARG DOCKER_REGISTRY

# ------------------
FROM python:3.9-slim-buster as both
# commands here apply to both prod and dev

RUN apt-get update
RUN pip install --upgrade pipenv

WORKDIR /usr/app/
EXPOSE 5000

# install service dependencies
RUN echo "Installing required build packages" && apt-get install -y gcc g++
COPY Pipfile* ./

# always install prod deps
RUN pipenv install --system --deploy --ignore-pipfile --verbose

RUN echo "Removing build packages" && apt-get remove -y gcc g++

# ------------------
FROM both AS dev-eq-0
# commands here only apply to prod environments

# ------------------
FROM both AS dev-eq-1
# commands here only apply to dev environments
RUN pipenv install --dev --system --deploy --ignore-pipfile --verbose


# ------------------
FROM dev-eq-${BUILD_DEV} AS final
# this is the final state of both images

# copy the app code
COPY . .
