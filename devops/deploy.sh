productName="tallulah"
resourceGroup="$productName-rg-$(openssl rand -hex 2)"
location="westus"
containerEnvName="$productName-env"
vnetName="$productName-vnet"
subnetName="default"

# If there is a env.sh file, source it
if [ -f env.sh ]; then
    source env.sh
fi

# Login to azure and set the subscription
az login --service-principal --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
az account set --subscription $AZURE_SUBSCRIPTION_ID

# Create a resource group
az group create --name $resourceGroup --location $location

# Create a virtual network
az network vnet create --resource-group $resourceGroup --name $vnetName --address-prefixes '10.0.0.0/16' --subnet-name $subnetName --subnet-prefix '10.0.0.0/20'
subnetId=$(az network vnet subnet show --resource-group $resourceGroup --vnet-name $vnetName --name $subnetName --query 'id' -o tsv)

# Create an container app environment
az containerapp env create -n $containerEnvName -g $resourceGroup --location $location --infrastructure-subnet-resource-id $subnetId
domainName=$(az containerapp env show -n $containerEnvName -g $resourceGroup --query 'properties.defaultDomain' -o tsv)

# Wait for the environment to be ready
while [ "$(az containerapp env show -n $containerEnvName -g $resourceGroup --query 'properties.provisioningState' -o tsv)" != "Succeeded" ]; do
    echo "Waiting for the environment to be ready..."
    sleep 5
done

# Deploy the backend app
az containerapp create \
  --name $productName-backend \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/backend:v0.1.0_72806d6 \
  --cpu 0.5 \
  --memory 1Gi \
  --target-port 8000 \
  --ingress 'external' \
  --min-replicas 1 \
  --env-vars \
      jwt_secret=$(openssl rand -hex 32) \
      refresh_secret=$(openssl rand -hex 32) \
      password_pepper=$(openssl rand -hex 32) \
      slack_webhook="" \
      outlook_client_id=$outlook_client_id \
      outlook_client_secret=$outlook_client_secret \
      outlook_redirect_uri=https://$productName-backend.$domainName/mailbox/authorize \
      outlook_tenant_id=$outlook_tenant_id \
      rabbit_mq_host=amqp://$rabbit_mq_user:$rabbit_mq_password@$productName-rabbitmq.$domainName \
      owner=prawal \
  --registry-server $container_registry_server \
  --registry-user $container_registry_user \
  --registry-password $container_registry_password

# Deploy the frontend app
az containerapp create \
  --name $productName-rabbitmq \
  --resource-group $resourceGroup \
  --environment $containerEnvName \
  --image $container_registry_server/$productName/rabbitmq:v0.1.0_72806d6 \
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
echo "##                                                              ##"
echo "##  The environment is ready!                                   ##"
echo "##                                                              ##"
echo "##  The backend app is available at:                            ##"
echo "##                                                              ##"
echo "##  https://$productName-backend.$domainName/                   ##"
echo "##                                                              ##"
echo "##  The frontend app is available at:                           ##"
echo "##                                                              ##"
echo "##  https://$productName-frontend.$domainName/                  ##"
echo "##                                                              ##"
echo "##  The resource group for the deployment is $resourceGroup     ##"
echo "##                                                              ##"
echo "##################################################################"
