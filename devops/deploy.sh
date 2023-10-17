#!/bin/bash

set -e

productName="tallulah"
resourceGroup="$productName-rg-$(openssl rand -hex 2)"
location="westus"
containerEnvName="$productName-env"
vnetName="$productName-vnet"
subnetName="default"
storageAccountName="tallulahstorage$(openssl rand -hex 4)"
keyVaultName="tallulahKeyvault$(openssl rand -hex 4)"

version=$(cat VERSION)
gitCommitHash=$(git rev-parse --short HEAD)
tag=v"$version"_"$gitCommitHash"

# If there is a .env file, source it
if [ -f .env ]; then
  set -o allexport
  source .env
  set +o allexport
fi


# Login to azure and set the subscription
az login --service-principal --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
az account set --subscription $AZURE_SUBSCRIPTION_ID


# Create a resource group
az group create --name $resourceGroup --location $location


# Create a virtual network
az network vnet create --resource-group $resourceGroup --name $vnetName --address-prefixes '10.0.0.0/16' --subnet-name $subnetName --subnet-prefix '10.0.0.0/20'
subnetId=$(az network vnet subnet show --resource-group $resourceGroup --vnet-name $vnetName --name $subnetName --query 'id' -o tsv)


# Create an container app environment without log analytics
az containerapp env create -n $containerEnvName -g $resourceGroup --location $location --infrastructure-subnet-resource-id $subnetId --logs-destination none
domainName=$(az containerapp env show -n $containerEnvName -g $resourceGroup --query 'properties.defaultDomain' -o tsv)
# Wait for the environment to be ready
while [ "$(az containerapp env show -n $containerEnvName -g $resourceGroup --query 'properties.provisioningState' -o tsv)" != "Succeeded" ]; do
    echo "Waiting for the environment to be ready..."
    sleep 5
done


# Check if the storage account name is available
while [ "$(az storage account check-name --name $storageAccountName --query 'nameAvailable' -o tsv)" != "true" ]; do
    echo "The storage account name is not available. Trying another name..."
    storageAccountName="tallulahStorage$(openssl rand -hex 4)"
done
# Create a storage account for the environment with version immutability
az storage account create --resource-group $resourceGroup --name $storageAccountName --location $location --kind StorageV2 --sku Standard_LRS --allow-blob-public-access false
# Wait for the storage account to be ready
while [ "$(az storage account show -n $storageAccountName -g $resourceGroup --query 'provisioningState' -o tsv)" != "Succeeded" ]; do
    echo "Waiting for the storage account to be ready..."
    sleep 5
done
storageAccountKey=$(az storage account keys list -n $storageAccountName --query "[0].value" -o tsv)
# Create a storage container for the environment
az storage container create --name mongo-backup --account-name $storageAccountName --account-key $storageAccountKey --public-access off
# Get the container HTTPS URL with SAS token
sas_token=$(az storage container generate-sas --name mongo-backup --account-name $storageAccountName --account-key $storageAccountKey --permissions dlrw --expiry 2025-01-01T00:00:00Z --output tsv)
connection_url="https://$storageAccountName.blob.core.windows.net/mongo-backup?$sas_token"


# Check if the keyvault name is available
while [ "$(az keyvault check-name --name $keyVaultName --query 'nameAvailable' -o tsv)" != "true" ]; do
    echo "The keyvault name is not available. Trying another name..."
    keyVaultName="tallulahKeyvault$(openssl rand -hex 4)"
done
# Create an azure key vault from the ARM template
az deployment group create --resource-group $resourceGroup --template-file keyvault.json --parameters \
    keyvault_name=$keyVaultName \
    azure_tenant_id=$AZURE_TENANT_ID \
    azure_object_id=$AZURE_OBJECT_ID \
    subnet_id=$subnetId
keyvault_url=$(az keyvault show -n $keyVaultName -g $resourceGroup --query 'properties.vaultUri' -o tsv)


# Create a mongodb container
az containerapp create \
  --name $productName-mongo \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/mongo:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 27017 \
  --transport 'tcp' \
  --ingress 'internal' \
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
      rabbit_mq_host=amqp://$rabbit_mq_user:$rabbit_mq_password@$productName-rabbitmq \
      mongodb_host=mongodb://$productName-mongo \
      jwt_secret=secretref:jwt-secret \
      refresh_secret=secretref:refresh-secret \
      password_pepper=secretref:password-pepper \
      outlook_client_id=secretref:outlook-client-id \
      outlook_client_secret=secretref:outlook-client-secret \
      AZURE_CLIENT_ID=secretref:azure-client-id \
      AZURE_CLIENT_SECRET=secretref:azure-client-secret \
      AZURE_TENANT_ID=secretref:azure-tenant-id \
      azure_keyvault_url=secretref:azure-keyvault-url \
      storage_container_sas_url=secretref:storage-container-sas-url \
  --secrets \
      jwt-secret=$(openssl rand -hex 32) \
      refresh-secret=$(openssl rand -hex 32) \
      password-pepper=$(openssl rand -hex 32) \
      outlook-client-id=$outlook_client_id \
      outlook-client-secret=$outlook_client_secret \
      azure-client-id=$AZURE_CLIENT_ID \
      azure-client-secret=$AZURE_CLIENT_SECRET \
      azure-tenant-id=$AZURE_TENANT_ID \
      azure-keyvault-url=$keyvault_url \
      storage-container-sas-url=$connection_url \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password


# Deploy the rabbitmq container
az containerapp create \
  --name $productName-rabbitmq \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/rabbitmq:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 5672 \
  --transport 'tcp' \
  --ingress 'internal' \
  --min-replicas 1 \
  --env-vars \
      RABBITMQ_DEFAULT_USER=$rabbit_mq_user \
      RABBITMQ_DEFAULT_PASS=$rabbit_mq_password \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password


# Deploy the classifier container
az containerapp create \
  --name $productName-classifier \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/classifier:v0.1.0_f374dff \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --env-vars \
      rabbit_mq_host=amqp://$rabbit_mq_user:$rabbit_mq_password@$productName-rabbitmq \
      mongodb_host=mongodb://$productName-mongo \
  --secrets \
      jwt-secret=$(openssl rand -hex 32) \
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
