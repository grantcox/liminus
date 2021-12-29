# Liminus gatekeeper / API proxy
This project is a python-based web API proxy, to be the only end-user entry point into our service architecture.  This service will:
 - be used by members of the public, authenticated end users, and authenticated staff members
 - manage a session for all these users, which will persist auth tokens and CSRF tokens
 - proxy requests to the appropriate backend (internal) services
 - support a flexible set of enabled backends, and backend middleware steps, so we can run this service in different contexts (eg a different deploy for staff vs public)
 - be the place where we strictly filter requests, eg:
   -- required auth tokens
   -- require CSRF tokens
   -- filter to acceptable request formats and headers
   -- parse and re-issue all request bodies
   -- filter response headers
   -- rate limit requests

The intention of this project is to replace our Tyk-based gatekeeper, as Tyk's python middleware support is very rudimentary, and leads to a poor overall experience (development, debugging, performance, and memory leaks).

## Boostrap your local environment

Run the following to bootstrap your local environment:

```sh
 `./scripts/bootstrap.sh`
```

The boostrap script will:

- Set up the `.env` file if it doesn't exist yet. We use the `.env` file to define environment variables. This file contains API keys, other secrets and other values that might be specific to your local environment so it is ignored in git. After changing `.env.template` it is a good idea to manually update your `.env` to reflect that change or deleting it and running `./scripts/bootstrap.sh` again.

- Add `local.liminus` to your machine's `/etc/hosts` file.

## Running it locally

To start the containers, run:

```sh
./scripts/up.sh
```

To stop the containers, run:

```sh
./scripts/down.sh
```

This will automatically setup the dependencies and run the server at https://local.liminus:8078. You can check to see that the service is running successfully by viewing https://local.liminus:8078/health/ping.

The uWSGI server can also be accessed directly without going through Traefik. To do that you can check the port on the host with `./scripts/docker-compose-local.sh ps`. You'll see output like this:

```sh
           Name                          Command               State            Ports
----------------------------------------------------------------------------------------------
local-liminus_app_1           uvicorn main:app --reload  ...   Up      0.0.0.0:61625->5000/tcp
...
```

In this example, the uvicorn server can be accessed through HTTP on port `61625`. An example URL would be http://localhost:61625/health/ping.
Please note this must be accessed via HTTP, not HTTPS - our TLS is terminated by Traefik which this method bypasses.
Have a look at [app/README.md](app/README.md) for service specific documentation.

### Debugging

To debug the application using VSCode, create a launch configuration ("Run -> Open Configurations") similar to the example below and adjust it to your workspace (relative paths).

```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Gatekeeper FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "cwd": "${workspaceFolder}/app",
            "args": [
                "main:app",
                "--reload",
                "--port",
                "8000"
            ],
        }
    ]
}
```

Attach to the debugger inside the container via F5 or selecting "Run -> Start Debugging".

## Helper scripts

We've got wrapper scripts around various docker compose commands to save typing. These scripts are located in the top-level `scripts` folder.

### Execute a command within a container:

```sh
./scripts/docker-compose-local.sh exec app pytest     # run pytest on the app service
./scripts/docker-compose-local.sh exec app /bin/bash  # shell into the app container
```

## Code quality

### Git hooks

We use the [pre-commit](https://pre-commit.com/) framework to manage pre-commit hooks. The `./scripts/bootstrap.sh` script automatically installs the pre-commit app and the actual hook in your repository.

### Auto-formatting / Static code analysis

We use [Black](https://black.readthedocs.io) for auto-formatting the code, which has [editor integrations](https://black.readthedocs.io/en/stable/editor_integration.html) for several tools including InelliJ IDEA, Vim, Visual Studio Code, Sublime, and more.

[Flake8](http://flake8.pycqa.org/) is a wrapper around PyFlakes, pycodestyle, and McCabe to maintain code style.

We also use [isort](https://pycqa.github.io/isort/) to automatically sort imports alphabetically and separate them into sections, which also has its own [editor integrations](https://github.com/pycqa/isort/wiki/isort-Plugins).

We use [Mypy](https://mypy.readthedocs.io/en/stable/) which is a static type checker and [Flake8](http://flake8.pycqa.org/) which is a wrapper around PyFlakes, pycodestyle, and McCabe to maintain code style.

