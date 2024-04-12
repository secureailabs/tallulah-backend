from app.data.operations import DatabaseOperations

data_service = DatabaseOperations()

organization_collection = "organizations"


async def org_name_to_id():
    # Create a mapping from organization_name to organization_id
    org_name_to_id = {}
    organizations = await data_service.find_by_query(collection=organization_collection, query={})
    for org in organizations:
        org_name_to_id[org["name"]] = org["_id"]

    # All the other collections that have the organization_name field
    collections_with_org_name = [
        "content-generation",
        "content-generation-template",
        "etapestry_repositories",
        "form_templates",
        "patient-profile-repository",
        "patient_profiles",
        "users",
    ]

    # Update documents in the documents collection
    for collection in collections_with_org_name:
        documents = await data_service.find_by_query(collection=collection, query={})
        for doc in documents:
            # Check if the organization_name in doc exists in the mapping
            if doc.get("organization") and doc["organization"] in org_name_to_id:
                # Update the document with the organization_id
                await data_service.update_one(
                    collection=collection,
                    query={"_id": doc["_id"]},
                    data={
                        "$set": {"organization_id": org_name_to_id[doc["organization"]]},
                        "$unset": {"organization": ""},
                    },
                )

        print(f"{collection} documents have been updated.")
