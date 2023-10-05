#!/bin/bash

productName="tallulah"
resourceGroup="$productName-rg-$(openssl rand -hex 2)"
# resourceGroup="tallulah-rg-291a"
location="westus"
containerEnvName="$productName-env"
vnetName="$productName-vnet"
subnetName="default"
storageAccountName="tallulahStorage$(openssl rand -hex 4)"

version=$(cat VERSION)
gitCommitHash=$(git rev-parse --short HEAD)
tag=v"$version"_"$gitCommitHash"

# If there is a .env file, source it
if [ -f .env ]; then
  set -o allexport
  source .env set
  +o allexport
fi

# Login to azure and set the subscription
az login \
  --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
az account set \
  --subscription $AZURE_SUBSCRIPTION_ID

# Create a resource group
az group create \
  --name $resourceGroup \
  --location $location

# Create a virtual network
az network vnet create \
  --resource-group $resourceGroup \
  --name $vnetName \
  --address-prefixes '10.0.0.0/16' \
  --subnet-name $subnetName \
  --subnet-prefix '10.0.0.0/20'
subnetId=$(az network vnet subnet show --resource-group $resourceGroup --vnet-name $vnetName --name $subnetName --query 'id' -o tsv)

# Create an container app environment
az containerapp env create -n $containerEnvName -g $resourceGroup --location $location --infrastructure-subnet-resource-id $subnetId
domainName=$(az containerapp env show -n $containerEnvName -g $resourceGroup --query 'properties.defaultDomain' -o tsv)

# Wait for the environment to be ready
while [ "$(az containerapp env show -n $containerEnvName -g $resourceGroup --query 'properties.provisioningState' -o tsv)" != "Succeeded" ]; do
    echo "Waiting for the environment to be ready..."
    sleep 5
done

# Create a storage account for the environment
# az storage account create \
#   --resource-group $resourceGroup \
#   --name $storageAccountName \
#   --location $location \
#   --kind StorageV2 \
#   --sku Standard_LRS \
#   --enable-large-file-share \
#   --query provisioningState

# Create a file share for mongodb
# storageShareName="mongodb"
# az storage share-rm create \
#   --resource-group $resourceGroup \
#   --storage-account $storageAccountName \
#   --name $storageShareName \
#   --quota 1024 \
#   --enabled-protocols SMB \
#   --output table

# storageAccountKey=$(az storage account keys list -n $storageAccountName --query "[0].value" -o tsv)

# storageMountName="mystoragemount"

# az containerapp env storage set \
#   --access-mode ReadWrite \
#   --azure-file-account-name $storageAccountName \
#   --azure-file-account-key $storageAccountKey \
#   --azure-file-share-name $storageShareName \
#   --storage-name $storageMountName \
#   --name $containerEnvName \
#   --resource-group $resourceGroup \
#   --output table

# Create a mongodb container
az containerapp create \
  --name $productName-mongo \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/mongo:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 27017 \
  --exposed-port 27017 \
  --transport 'tcp' \
  --ingress 'external' \
  --min-replicas 1 \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password
  # --env-vars \
  #     MONGO_INITDB_ROOT_USERNAME=$mongo_user \
  # --secrets \
  #     MONGO_INITDB_ROOT_PASSWORD=$mongo_password \


# az containerapp show \
#   --name $CONTAINER_APP_NAME \
#   --resource-group $RESOURCE_GROUP \
#   --output yaml > app.yaml

# ./yq '.properties.template.volumes += [{"name": "azure-files-volume", "storageType": "AzureFile", "storageName": "mystorage"}]' app.yaml > app.yaml
# ./yq '.properties.template.containers.volumeMounts += [{"volumeName": "azure-files-volume", "mountPath": "AzureFile"}]' app.yaml > app.yaml

# az containerapp update \
#   --name $CONTAINER_APP_NAME \
#   --resource-group $RESOURCE_GROUP \
#   --yaml app.yaml \
#   --output table


# Deploy the backend app
az containerapp create \
  --name $productName-backend \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/backend:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 8000 \
  --ingress 'external' \
  --min-replicas 1 \
  --env-vars \
      slack_webhook="" \
      outlook_redirect_uri=https://$productName-backend.$domainName/mailbox/authorize \
      outlook_tenant_id=$outlook_tenant_id \
      rabbit_mq_host=amqp://$rabbit_mq_user:$rabbit_mq_password@$productName-rabbitmq.$domainName \
      mongodb_host=mongodb://$productName-mongo.$domainName \
      jwt_secret=secretref:jwt-secret \
      refresh_secret=secretref:refresh-secret \
      password_pepper=secretref:password-pepper \
      outlook_client_id=secretref:outlook-client-id \
      outlook_client_secret=secretref:outlook-client-secret \
  --secrets \
      jwt-secret=$(openssl rand -hex 32) \
      refresh-secret=$(openssl rand -hex 32) \
      password-pepper=$(openssl rand -hex 32) \
      outlook-client-id=$outlook_client_id \
      outlook-client-secret=$outlook_client_secret \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password

# Deploy the frontend app
az containerapp create \
  --name $productName-rabbitmq \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/rabbitmq:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 5672 \
  --exposed-port 5672 \
  --transport 'tcp' \
  --ingress 'external' \
  --min-replicas 1 \
  --env-vars \
      RABBITMQ_DEFAULT_USER=$rabbit_mq_user \
      RABBITMQ_DEFAULT_PASS=$rabbit_mq_password \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password


echo "##################################################################"
echo "##                                                                "
echo "##  The environment is ready!                                     "
echo "##                                                                "
echo "##  The backend app is available at:                              "
echo "##                                                                "
echo "##  https://$productName-backend.$domainName/                     "
echo "##                                                                "
echo "##  The frontend app is available at:                             "
echo "##                                                                "
echo "##  https://$productName-frontend.$domainName/                    "
echo "##                                                                "
echo "##  The resource group for the deployment is $resourceGroup       "
echo "##                                                                "
echo "##################################################################"
