# SAIL API Services Portal
Set the environment variables in the .env file before running the application

## Architecture Notes
The application is build to run as a monolithic application with only one instance.
There is future work to make the application stateless and horizontally scalable.
There is a app/utils/lock_store.py file that is used to store the locks on the resources. This is a in-memory store and is not scalable.
If the application is to be made stateless, the lock store should be replaced with a distributed lock store like Redis.

## Developer Virtual Environment
To get started with the developemt environment, build a virtual development environment and install all the requirements using:
`poetry shell`
`poetry install`

## Local deployment

### Build the docker images

```
make build_image
```

### Run the docker images

```
make run_image
```
This will run the backend, mongodb and rabbitmq containers locally. The backend container will be available on localhost port 8000.


### API documentation
The api is automatically generated from the openapi spec which can be found on http(s)://<hostname>:8000/docs
The static generated redoc html documentatation html file is also available in docs/index.html which can be viewed in a browser.

#### Typescript client and Python client SDKs
```
npm install
make generate_client
```
This will generate the client sdk for typescript and python and place them in the generated directory.
The above code expects node and npm to be installed before hand. After node and npm are installed, run the following commands:
Make sure to activate the virtual environment before running the generator script and update the IP address in the script to point to the api server.

## Publish Docker images to Azure Container Registry
Build the docker image using:
`make build_image`

Push the docker image to the docker registry using:
`make push_all`

Note: export the following values before pushing:
```
export AZURE_SUBSCRIPTION_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AZURE_TENANT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AZURE_CLIENT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AZURE_CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export DOCKER_REGISTRY_NAME="developmentdockerregistry"
```

