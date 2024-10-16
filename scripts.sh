#!/bin/bash
set -e
set -x

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    MSYS_NT*)   machine=Git;;
    *)          machine="UNKNOWN:${unameOut}"
esac

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
    docker build -t $1 --platform linux/amd64 .

    # Tag the rabbitmq image
    docker pull rabbitmq:3 --platform linux/amd64
    docker tag rabbitmq:3 tallulah/rabbitmq

    # Build the logstash image
    docker build . -f devops/docker/logstash/Dockerfile -t tallulah/logstash --platform linux/amd64
}

# Run the docker image
run_image() {

    check_docker

    # Create a network if it doesn't exist
    if ! docker network ls | grep -q "tallulah"; then
        docker network create tallulah
    fi

    # Run rabbitmq if not already running
    if ! docker ps | grep -q "rabbitmq"; then
        docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 --network tallulah rabbitmq:3-management
    fi

    # Run the backend image
    # docker run -it --name backend -p 8000:8000 -v $(pwd)/app:/app --network tallulah --env-file .env --entrypoint "uvicorn app.main:server --host 0.0.0.0 --port 8000 --reload"  tallulah/backend
    docker run -d --rm --name backend -p 8000:8000 -v $(pwd)/app:/app --network tallulah --env-file .env tallulah/backend --platform linux/amd64
}


stop_backend() {
    # Stop and remove the backend container
    docker stop backend
}

stop_all() {
    # Stop and remove all the containers
    docker stop backend rabbitmq
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
    wget http://127.0.0.1:8000/api/openapi.json -P docs/ --no-check-certificate

    # Rename all "_id" in openapi.json to "id"
    # This is done because the openapi spec generates the keys of the models with "_id" instead of "id"
    # It is not a bug, it happens because the openapi spec uses alias of the keys used in the models
    # For example, if a model has a field called "id", it will be renamed to "_id", because that's what mongodb uses
    # But _is is considered a private member so "id" is used instead
    sed -i '' 's/\"_id\"/\"id\"/g' docs/openapi.json

    # Generate the python client
    rm -rf tallulah-client/
    # openapi-python-client --version
    # openapi-python-client generate --path docs/openapi.json

    # Generate a whl package for the client using the pyproject.toml file
    # pushd tallulah-client
    # poetry build
    # popd

    # Generate the typescript client
    rm -rf tallulah-client-ts/
    npm run generate-client

    popd
}

deploy() {
    az login
    make build_image
    make push_all

    version=$(cat VERSION)
    gitCommitHash=$(git rev-parse --short HEAD)
    backend_tag=v"$version"_"$gitCommitHash"
    echo "Tag: $backend_tag"

    # rm -rf researcher-ui || true
    # git clone git@github.com:secureailabs/researcher-ui.git
    pushd researcher-ui
    yarn
    yarn build:beta
    make build_image
    make push_image

    version=$(cat VERSION)
    gitCommitHash=$(git rev-parse --short HEAD)
    ui_tag=v"$version"_"$gitCommitHash"
    echo "Tag: $ui_tag"
    popd

    pushd devops/terraform
    if [ $machine == "Mac" ]; then
        sed -i '' "s/^backend_container_image_tag=.*/backend_container_image_tag=\"tallulah\/backend:$backend_tag\"/g" development.tfvars
        sed -i '' "s/^ui_container_image_tag=.*/ui_container_image_tag=\"tallulah\/ui:$ui_tag\"/g" development.tfvars
        sed -i '' "s/^rabbitmq_container_image_tag=.*/rabbitmq_container_image_tag=\"tallulah\/rabbitmq:$backend_tag\"/g" development.tfvars
        sed -i '' "s/^logstash_container_image_tag=.*/logstash_container_image_tag=\"tallulah\/logstash:$backend_tag\"/g" development.tfvars
    else
        sed -i "s/^backend_container_image_tag=.*/backend_container_image_tag=\"tallulah\/backend:$backend_tag\"/g" development.tfvars
        sed -i "s/^ui_container_image_tag=.*/ui_container_image_tag=\"tallulah\/ui:$ui_tag\"/g" development.tfvars
        sed -i "s/^rabbitmq_container_image_tag=.*/rabbitmq_container_image_tag=\"tallulah\/rabbitmq:$backend_tag\"/g" development.tfvars
        sed -i "s/^logstash_container_image_tag=.*/logstash_container_image_tag=\"tallulah\/logstash:$backend_tag\"/g" development.tfvars
    fi

    az account set --subscription $AZURE_SUBSCRIPTION_ID
    terraform init -backend-config="backend.tfvars" -reconfigure
    terraform apply -var-file="development.tfvars" -auto-approve
    popd
}


release() {
    az login
    make build_image
    make push_all

    version=$(cat VERSION)
    gitCommitHash=$(git rev-parse --short HEAD)
    backend_tag=v"$version"_"$gitCommitHash"
    echo "Tag: $backend_tag"

    # rm -rf researcher-ui || true
    # git clone git@github.com:secureailabs/researcher-ui.git
    pushd researcher-ui
    yarn
    yarn build
    make build_image
    make push_image

    version=$(cat VERSION)
    gitCommitHash=$(git rev-parse --short HEAD)
    ui_tag=v"$version"_"$gitCommitHash"
    echo "Tag: $ui_tag"
    popd

    pushd devops/terraform
    sed -i '' "s/^backend_container_image_tag=.*/backend_container_image_tag=\"tallulah\/backend:$backend_tag\"/g" production.tfvars
    sed -i '' "s/^ui_container_image_tag=.*/ui_container_image_tag=\"tallulah\/ui:$ui_tag\"/g" production.tfvars
    sed -i '' "s/^rabbitmq_container_image_tag=.*/rabbitmq_container_image_tag=\"tallulah\/rabbitmq:$backend_tag\"/g" production.tfvars
    sed -i '' "s/^logstash_container_image_tag=.*/logstash_container_image_tag=\"tallulah\/logstash:$backend_tag\"/g" production.tfvars

    az account set --subscription $AZURE_SUBSCRIPTION_ID
    terraform init -backend-config="backend_prod.tfvars" -reconfigure
    # export AZURE_SUBSCRIPTION_ID="b7a46052-b7b1-433e-9147-56efbfe28ac5"
    # az account set --subscription $AZURE_SUBSCRIPTION_ID
    terraform apply -var-file="production.tfvars"
    popd
}


# run whatever command is passed in as arguments
$@
