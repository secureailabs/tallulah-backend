#!/bin/bash

set -euo pipefail

productName="tallulah"
deployment_id="$(openssl rand -hex 4)"
resourceGroup="$productName-rg-$deployment_id"
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
# Add Storage and keyvault to subnet service endpoints
az network vnet subnet update --resource-group $resourceGroup --vnet-name $vnetName --name $subnetName --service-endpoints 'Microsoft.Storage' 'Microsoft.KeyVault'

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
az storage account create --resource-group $resourceGroup --name $storageAccountName --location $location --kind StorageV2 --sku Standard_LRS --subnet $subnetId
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


# Deploy the backend app
# outlook_redirect_uri=https://$productName-backend.$domainName/mailbox/authorize \
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
      outlook_redirect_uri=$outlook_redirect_uri \
      outlook_tenant_id=$outlook_tenant_id \
      mongo_db_name=tallulah-$deployment_id \
      mongo_connection_url=secretref:mongo-connection-url \
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
      rabbit_mq_queue_name=email_queue \
      rabbit_mq_host=secretref:rabbit-mq-host \
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
      mongo-connection-url=mongodb+srv://$mongo_atlas_user:$mongo_atlas_password@$mongo_atlas_host \
      rabbit-mq-host=amqp://$rabbit_mq_user:$rabbit_mq_password@$productName-rabbitmq \
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
  --image $container_registry_server/$productName/classifier:v0.1.0_7f67c94 \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --env-vars \
      rabbit_mq_port=5672 \
      rabbit_mq_queue_name=email_queue \
      rabbit_mq_hostname=secretref:rabbit-mq-host \
      mongo_db_name=tallulah-$deployment_id \
      mongo_connection_url=secretref:mongo-connection-url \
      mongodb_collection_name=emails \
  --secrets \
      mongo-connection-url=mongodb+srv://$mongo_atlas_user:$mongo_atlas_password@$mongo_atlas_host \
      rabbit-mq-host=amqp://$rabbit_mq_user:$rabbit_mq_password@$productName-rabbitmq \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password


# Deploy the frontend app
az containerapp create \
  --name $productName-ui \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/ui:v0.1.0_089fdcb \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 80 \
  --ingress 'external' \
  --min-replicas 1 \
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
