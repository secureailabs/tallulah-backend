# SAIL API Services Portal

Set the following environment variables in the .env file before running the application:
```
export AZURE_SUBSCRIPTION_ID="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export AZURE_TENANT_ID="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export AZURE_CLIENT_ID="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export AZURE_CLIENT_SECRET="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export AZURE_OBJECT_ID="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export container_registry_server="XXXXXXXXXXXXXXXXXXXXXXXXXXXXX.azurecr.io"
export container_registry_user="XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
export container_registry_password="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export outlook_client_id="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export outlook_client_secret="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export outlook_tenant_id="b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0"
export rabbit_mq_user="user"
export rabbit_mq_password="password"
```

## Developer Virtual Environment
To get started with the developemt environment, build a virtual development environment and install all the requirements using:
`poetry shell`
`poetry install`

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
```
```
Make sure to activate the virtual environment before running the generator script and update the IP address in the script to point to the api server.

## Deployment
Build the docker image using:
`make build_image`

Push the docker image to the docker registry using:
`make push_image`
Note: export the following values before pushing:
```
export AZURE_SUBSCRIPTION_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AZURE_TENANT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AZURE_CLIENT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AZURE_CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export DOCKER_REGISTRY_NAME="developmentdockerregistry"
```

## Local deployment

### Build the docker images

```
make build_image
```

### Run the docker images

```
make run_image
```

## Api Writing Guidelines
- Endpoint decorator should be defined in the format '@api.route('/<resource_name>/<id>/<sub_resource>/<id>.../?query_params')'
- Endpoint decorator should at least contain description, response_description, operation_id, response_model, status_code
- APIs should return same type of objects for every success response, the response codes can be different though
- Endpoint decorator should contain response_model if the response is a json object
- If there are path parameters, they should have a description in the function definition
- If there are query parameters, they should have a description in the function definition


Example of a good endpoint decorator:
```python
@router.get(
    path="/data-federations",
    description="Get list of all the data federations",
    response_description="List of data federations",
    response_model=GetMultipleDataFederation_Out,
    response_model_by_alias=False,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    tags=["Data Federations"],
    operation_id="get_all_data_federations",
)
async def get_all_data_federations(
    data_submitter_id: Optional[PyObjectId] = Query(default=None, description="UUID of Data Submitter in the data federation"),
    researcher_id: Optional[PyObjectId] = Query(default=None, description="UUID of Researcher in the data federation"),
    dataset_id: Optional[PyObjectId] = Query(default=None, description="UUID of Dataset in the data federation"),
    current_user: TokenData = Depends(get_current_user),
) -> GetMultipleDataFederation_Out:
```
