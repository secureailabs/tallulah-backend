# Release Process

## Build and publish a new version
1. Make sure all changes are commited
2. Update the docker image tags in the devops/deploy.sh file
3. Update the version in the VERSION file according to [Semantic Versioning](https://semver.org/)
4. Update/Create the values in the .env file
5. Add the release notes to the CHANGELOG.md file in the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
6. Commit the changes and call this commit "Release <version>"
7. Tag the commit using `git tag "<version>"` with the version number and push the tag to the remote repository using `git push --tags`
8. Run `make deploy -j4` to build and push docker images to registry. This will also create create a new resource group on Azure and deploy the docker images to the resource group as container images

## Manual Steps

### Update the frontend DNS records
1. Go to Azure Portal and look for the frontned container app in the newly created resource group
2. Go to the custom domains section and copy the frontend DNS records
3. Create a new custom domain using the managed certificate and <customer_name>.tallulah.ai as Domain value
4. Go to the DNS provider(GoDaddy) and update the DNS records to point to the new frontend container app. Primarily the CNAME and TXT records need to be updated. Use <customer_name> and asuid.<customer_name> as the values for the CNAME and TXT records respectively.
5. Wait for azure to create the SSL certificate for the new custom domain. This can be checked in the custom domains section of the frontend container app in the azure portal.

### Update the backend DNS records
1. Go to Azure Portal and look for the backend container app in the newly created resource group
2. Go to the custom domains section and copy the backend DNS records
3. Create a new custom domain using the managed certificate and api.<customer_name>.tallulah.ai as Domain value
4. Go to the DNS provider(GoDaddy) and update the DNS records to point to the new backend container app. Primarily the CNAME and TXT records need to be updated. Use api.<customer_name> and asuid.api.<customer_name> as the values for the CNAME and TXT records respectively.
5. Wait for azure to create the SSL certificate for the new custom domain. This can be checked in the custom domains section of the backend container app in the azure portal.

### Add a private endpoint and user to the mongodb atlas cluster
1. Go to the mongodb atlas cluster `tallulah-prod`
2. Click on Network Access and add a new private endpoint following the steps provided by mongodb atlas
3. Add a new user to the cluster with readWriteAnyDatabase role if not already exists

### Update the URL in the Azure AD app registration
1. Go to Azure Portal and look for the Azure AD app registration by the name `test-email-prawal`
2. Go to the Authentication section and update the Redirect URI to the new frontend URL
3. Save the changes
