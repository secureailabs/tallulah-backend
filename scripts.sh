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

# Set the environment variables
set_env_vars() {
    # If there is a env.sh file, source it
    if [ -f env.sh ]; then
        source env.sh
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
    docker build -t $1 -f "docker/Dockerfile" .

    # Tag the rabbitmq image
    docker pull rabbitmq:3
    docker tag rabbitmq:3 tallulah/rabbitmq
}

# Run the docker image
run_image() {

    check_docker
    set_env_vars

    docker run -it \
    -p 8000:8000 \
    -v $(pwd)/app:/app \
    --env slack_webhook=$slack_webhook \
    --env owner=$owner \
    --env jwt_secret=$jwt_secret \
    --env password_pepper=$password_pepper \
    --env refresh_secret=$refresh_secret \
    --env outlook_client_id=$outlook_client_id \
    --env outlook_client_secret=$outlook_client_secret \
    --env outlook_redirect_uri=$outlook_redirect_uri \
    $1
}

run() {
    set_env_vars
    uvicorn app.main:server --reload
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
    rm -rf sail-client/
    openapi-python-client generate --path docs/openapi.json

    # Generate a whl package for the client using the pyproject.toml file
    pushd sail-client
    poetry build
    popd

    popd
}

# run whatever command is passed in as arguments
$@
