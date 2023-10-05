#!/bin/bash
set -e
set -x

# Check if docker is installed
check_docker() {
    docker --version
    retVal=$?
    if [ $retVal -ne 0 ]; then
        echo "Error docker does not exist"
        exit $retVal
    fi
}

# function to tag and push the input image to the docker hub
push_image_to_registry() {
    # check docker installed
    check_docker

    # check if the DOCKER_REGISTRY_NAME is set
    if [ -z "$DOCKER_REGISTRY_NAME" ]; then
        echo "DOCKER_REGISTRY_NAME is not set"
        exit 1
    fi

    echo "login to azure account"
    az login --service-principal --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
    az account set --subscription $AZURE_SUBSCRIPTION_ID

    echo "log in to azure registry"
    az acr login --name "$DOCKER_REGISTRY_NAME"

    # Get the version from the ../VERSION file
    version=$(cat VERSION)

    # Get the current git commit hash
    gitCommitHash=$(git rev-parse --short HEAD)

    echo "Tag and Pushing image to azure hub"
    tag=v"$version"_"$gitCommitHash"
    echo "Tag: $tag"
    docker tag "$1" "$DOCKER_REGISTRY_NAME".azurecr.io/"$1":"$tag"
    docker push "$DOCKER_REGISTRY_NAME".azurecr.io/"$1":"$tag"
    echo Image url: "$DOCKER_REGISTRY_NAME".azurecr.io/"$1":"$tag"
}

# Function to build image
build_image() {
    check_docker
    poetry export -f requirements.txt --output requirements.txt --without-hashes
    docker build -t $1 -f "Dockerfile" .

    # Tag the rabbitmq image
    docker pull rabbitmq:3
    docker tag rabbitmq:3 tallulah/rabbitmq

    # Tag the mongodb image
    docker pull mongo:6.0
    docker tag mongo:6.0 tallulah/mongo
}

# Run the docker image
run_image() {

    check_docker

    # Create a network if it doesn't exist
    if ! docker network ls | grep -q "tallulah"; then
        docker network create tallulah
    fi

    # Run mongo if not already running
    if ! docker ps | grep -q "mongo"; then
        docker run -d --name mongo -p 27017:27017 --network tallulah mongo:6.0
    fi

    # Run rabbitmq if not already running
    if ! docker ps | grep -q "rabbitmq"; then
        docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 --network tallulah rabbitmq:3-management
    fi

    # Run the backend image
    docker run -it -p 8000:8000 -v $(pwd)/app:/app --network tallulah --env-file .env tallulah/backend
}

run() {
    uvicorn app.main:server --reload --env-file .env
}

generate_client() {
    generatedDir="generated"

    # Create the generated folder if it doesn't exist
    mkdir -p $generatedDir

    pushd $generatedDir

    # delete existing openapi.json
    rm -f docs/openapi.json

    # Download the API spec
    wget http://127.0.0.1:8000/openapi.json -P docs/ --no-check-certificate

    # Rename all "_id" in openapi.json to "id"
    # This is done because the openapi spec generates the keys of the models with "_id" instead of "id"
    # It is not a bug, it happens because the openapi spec uses alias of the keys used in the models
    # For example, if a model has a field called "id", it will be renamed to "_id", because that's what mongodb uses
    # But _is is considered a private member so "id" is used instead
    sed -i 's/\"_id\"/\"id\"/g' docs/openapi.json

    # Generate the python client
    rm -rf tallulah-client/
    openapi-python-client --version
    openapi-python-client generate --path docs/openapi.json

    # Generate a whl package for the client using the pyproject.toml file
    pushd tallulah-client
    poetry build
    popd

    # Generate the typescript client
    rm -rf tallulah-client-ts/
    npm run generate-client

    popd
}

# run whatever command is passed in as arguments
$@
