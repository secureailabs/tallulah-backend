from fastapi.encoders import jsonable_encoder

from app.data.operations import DatabaseOperations
from app.utils.elastic_search import ElasticsearchClient


async def move_data_from_mongo_to_es():
    data_service = DatabaseOperations()
    es_client = ElasticsearchClient()

    # Documents template collection and actual data collection
    form_template_collection = "form_templates"
    form_data_collection = "form_data"

    # Get all the form templates
    form_templates = await data_service.find_by_query(collection=form_template_collection, query={})

    for form_template in form_templates:
        # Check if the index exists
        index_exists = await es_client.index_exists(index_name=str(form_template["_id"]))
        if not index_exists:
            continue

        # Check if the existing index documents have the creation date
        already_migrated = False
        documents = await es_client.search(index_name=str(form_template["_id"]), search_query="*")
        for document in documents["hits"]["hits"]:
            if "creation_time" in document["_source"]:
                print(
                    f"Form data for the form template {form_template['_id']} already has the creation time. Skipping..."
                )
                already_migrated = True
                break

        if already_migrated:
            continue

        # Delete the existing index
        await es_client.delete_index(index_name=str(form_template["_id"]))

        # Create a new index
        await es_client.create_index(index_name=str(form_template["_id"]))

        # Get the form data for the form template
        form_data = await data_service.find_by_query(
            collection=form_data_collection,
            query={"form_template_id": form_template["_id"], "state": {"$ne": "DELETED"}},
        )

        # Insert the form data into the Elasticsearch
        for data in form_data:
            await es_client.insert_document(
                index_name=str(form_template["_id"]),
                id=str(data["_id"]),
                document=jsonable_encoder(data, exclude=set(["_id", "id"])),
            )

        print(f"Form data for the form template {form_template['_id']} has been moved to Elasticsearch.")
