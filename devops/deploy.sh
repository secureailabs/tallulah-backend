#!/bin/bash

set -euo pipefail

product_name="tallulah"
deployment_id="$(openssl rand -hex 4)"
resource_group="$product_name-rg-$deployment_id"
location="westus"
container_env_name="$product_name-env"
vnet_name="$product_name-vnet"
subnet_name="default"
storage_account_name="tallulahstorage$(openssl rand -hex 4)"
key_vault_name="tallulahKeyvault$(openssl rand -hex 4)"

version=$(cat VERSION)
git_commit_hash=$(git rev-parse --short HEAD)
tag=v"$version"_"$git_commit_hash"

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
az group create --name $resource_group --location $location


# Create a virtual network
az network vnet create --resource-group $resource_group --name $vnet_name --address-prefixes '10.0.0.0/16' --subnet-name $subnet_name --subnet-prefix '10.0.0.0/20'
subnetId=$(az network vnet subnet show --resource-group $resource_group --vnet-name $vnet_name --name $subnet_name --query 'id' -o tsv)
# Add Storage and keyvault to subnet service endpoints
az network vnet subnet update --resource-group $resource_group --vnet-name $vnet_name --name $subnet_name --service-endpoints 'Microsoft.Storage' 'Microsoft.KeyVault'

# Create an container app environment without log analytics
az containerapp env create -n $container_env_name -g $resource_group --location $location --infrastructure-subnet-resource-id $subnetId --logs-destination none
domain_name=$(az containerapp env show -n $container_env_name -g $resource_group --query 'properties.defaultDomain' -o tsv)
# Wait for the environment to be ready
while [ "$(az containerapp env show -n $container_env_name -g $resource_group --query 'properties.provisioningState' -o tsv)" != "Succeeded" ]; do
    echo "Waiting for the environment to be ready..."
    sleep 5
done


# Check if the storage account name is available
while [ "$(az storage account check-name --name $storage_account_name --query 'nameAvailable' -o tsv)" != "true" ]; do
    echo "The storage account name is not available. Trying another name..."
    storage_account_name="tallulahStorage$(openssl rand -hex 4)"
done
# Create a storage account for the environment with version immutability
az storage account create --resource-group $resource_group --name $storage_account_name --location $location --kind StorageV2 --sku Standard_LRS --subnet $subnetId
# Wait for the storage account to be ready
while [ "$(az storage account show -n $storage_account_name -g $resource_group --query 'provisioningState' -o tsv)" != "Succeeded" ]; do
    echo "Waiting for the storage account to be ready..."
    sleep 5
done
storageAccountKey=$(az storage account keys list -n $storage_account_name --query "[0].value" -o tsv)
# Create a storage container for the environment
az storage container create --name mongo-backup --account-name $storage_account_name --account-key $storageAccountKey --public-access off
# Get the container HTTPS URL with SAS token
sas_token=$(az storage container generate-sas --name mongo-backup --account-name $storage_account_name --account-key $storageAccountKey --permissions dlrw --expiry 2025-01-01T00:00:00Z --output tsv)
connection_url="https://$storage_account_name.blob.core.windows.net/mongo-backup?$sas_token"


# Check if the keyvault name is available
while [ "$(az keyvault check-name --name $key_vault_name --query 'nameAvailable' -o tsv)" != "true" ]; do
    echo "The keyvault name is not available. Trying another name..."
    key_vault_name="tallulahKeyvault$(openssl rand -hex 4)"
done
# Create an azure key vault from the ARM template
az deployment group create --resource-group $resource_group --template-file keyvault.json --parameters \
    keyvault_name=$key_vault_name \
    azure_tenant_id=$AZURE_TENANT_ID \
    azure_object_id=$AZURE_OBJECT_ID \
    subnet_id=$subnetId
keyvault_url=$(az keyvault show -n $key_vault_name -g $resource_group --query 'properties.vaultUri' -o tsv)


# Deploy the backend app
# OUTLOOK_REDIRECT_URI=https://$product_name-backend.$domain_name/mailbox/authorize \
# OUTLOOK_REDIRECT_URI=$OUTLOOK_REDIRECT_URI \
az containerapp create \
  --name $product_name-backend \
  --resource-group $resource_group \
  --environment $container_env_name \
  --image $CONTAINER_REGISTRY_SERVER/$product_name/backend:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 8000 \
  --ingress 'external' \
  --min-replicas 1 \
  --env-vars \
      SLACK_WEBHOOK="" \
      OUTLOOK_REDIRECT_URI=https://$product_name-backend.$domain_name/mailbox/authorize \
      OUTLOOK_TENANT_ID=$OUTLOOK_TENANT_ID \
      MONGO_DB_NAME=tallulah-$deployment_id \
      MONGO_CONNECTION_URL=secretref:mongo-connection-url \
      JWT_SECRET=secretref:jwt-secret \
      REFRESH_SECRET=secretref:refresh-secret \
      PASSWORD_PEPPER=secretref:password-pepper \
      OUTLOOK_CLIENT_ID=secretref:outlook-client-id \
      OUTLOOK_CLIENT_SECRET=secretref:outlook-client-secret \
      AZURE_CLIENT_ID=secretref:azure-client-id \
      AZURE_CLIENT_SECRET=secretref:azure-client-secret \
      AZURE_TENANT_ID=secretref:azure-tenant-id \
      AZURE_KEYVAULT_URL=secretref:azure-keyvault-url \
      STORAGE_CONTAINER_SAS_URL=secretref:storage-container-sas-url \
      RABBIT_MQ_QUEUE_NAME=email_queue \
      RABBIT_MQ_HOST=secretref:rabbit-mq-host \
      TALLULAH_ADMIN_PASSWORD=secretref:tallulah-admin-password \
  --secrets \
      jwt-secret=$(openssl rand -hex 32) \
      refresh-secret=$(openssl rand -hex 32) \
      password-pepper=$(openssl rand -hex 32) \
      outlook-client-id=$OUTLOOK_CLIENT_ID \
      outlook-client-secret=$OUTLOOK_CLIENT_SECRET \
      azure-client-id=$AZURE_CLIENT_ID \
      azure-client-secret=$AZURE_CLIENT_SECRET \
      azure-tenant-id=$AZURE_TENANT_ID \
      azure-keyvault-url=$keyvault_url \
      storage-container-sas-url=$connection_url \
      mongo-connection-url=mongodb+srv://$MONGO_ATLAS_USER:$MONGO_ATLAS_PASSWORD@$MONGO_ATLAS_HOST \
      rabbit-mq-host=amqp://$RABBIT_MQ_USER:$RABBIT_MQ_PASSWORD@$product_name-rabbitmq \
      tallulah-admin-password=$(openssl rand -hex 16) \
  --registry-server $CONTAINER_REGISTRY_SERVER \
  --registry-user $CONTAINER_REGISTRY_USER \
  --registry-password $CONTAINER_REGISTRY_PASSWORD


# Deploy the rabbitmq container
az containerapp create \
  --name $product_name-rabbitmq \
  --resource-group $resource_group \
  --environment $container_env_name \
  --image $CONTAINER_REGISTRY_SERVER/$product_name/rabbitmq:$tag \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 5672 \
  --transport 'tcp' \
  --ingress 'internal' \
  --min-replicas 1 \
  --env-vars \
      RABBITMQ_DEFAULT_USER=$RABBIT_MQ_USER \
      RABBITMQ_DEFAULT_PASS=$RABBIT_MQ_PASSWORD \
  --registry-server $CONTAINER_REGISTRY_SERVER \
  --registry-user $CONTAINER_REGISTRY_USER \
  --registry-password $CONTAINER_REGISTRY_PASSWORD

# Deploy the classifier container
az containerapp create \
  --name $product_name-classifier \
  --resource-group $resource_group \
  --environment $container_env_name \
  --image $CONTAINER_REGISTRY_SERVER/$product_name/classifier:v0.1.0_45f3430 \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --env-vars \
      RABBIT_MQ_PORT=5672 \
      RABBIT_MQ_QUEUE_NAME=email_queue \
      RABBIT_MQ_HOSTNAME=secretref:rabbit-mq-host \
      MONGO_DB_NAME=tallulah-$deployment_id \
      MONGO_CONNECTION_URL=secretref:mongo-connection-url \
      MONGODB_COLLECTION_NAME=emails \
  --secrets \
      mongo-connection-url=mongodb+srv://$MONGO_ATLAS_USER:$MONGO_ATLAS_PASSWORD@$MONGO_ATLAS_HOST \
      rabbit-mq-host=amqp://$RABBIT_MQ_USER:$RABBIT_MQ_PASSWORD@$product_name-rabbitmq \
  --registry-server $CONTAINER_REGISTRY_SERVER \
  --registry-user $CONTAINER_REGISTRY_USER \
  --registry-password $CONTAINER_REGISTRY_PASSWORD


# Deploy the frontend app
az containerapp create \
  --name $product_name-ui \
  --resource-group $resource_group \
  --environment $container_env_name \
  --image $CONTAINER_REGISTRY_SERVER/$product_name/ui:v0.1.0_089fdcb \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 80 \
  --ingress 'external' \
  --min-replicas 1 \
  --registry-server $CONTAINER_REGISTRY_SERVER \
  --registry-user $CONTAINER_REGISTRY_USER \
  --registry-password $CONTAINER_REGISTRY_PASSWORD

echo "##################################################################"
echo "##                                                                "
echo "##  The environment is ready!                                     "
echo "##                                                                "
echo "##  The backend app is available at:                              "
echo "##                                                                "
echo "##  https://$product_name-backend.$domain_name/                     "
echo "##                                                                "
echo "##  The frontend app is available at:                             "
echo "##                                                                "
echo "##  https://$product_name-frontend.$domain_name/                    "
echo "##                                                                "
echo "##  The resource group for the deployment is $resource_group       "
echo "##                                                                "
echo "##################################################################"
