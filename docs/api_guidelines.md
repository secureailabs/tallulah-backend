# Api Writing Guidelines
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
