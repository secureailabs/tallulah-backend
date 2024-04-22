from elasticsearch import AsyncElasticsearch


class ElasticsearchClient:
    _instance = None

    def __new__(cls, cloud_id=None, password=None):
        if cls._instance is None:
            if cloud_id is None or password is None:
                raise Exception("cloud_id and password must be provided")
            cls._instance = super(ElasticsearchClient, cls).__new__(cls)
            cls.client = AsyncElasticsearch(cloud_id=cloud_id, basic_auth=("elastic", password))
        return cls._instance

    async def create_index(self, index_name: str, raise_on_already_exist: bool = False):
        resp = await self.client.indices.exists(index=index_name)
        if resp:
            if raise_on_already_exist:
                raise Exception(f"Index {index_name} already exists")
            else:
                print(f"Index {index_name} already exists. Skipping creation...")
                return

        resp = await self.client.indices.create(index=index_name)

        return resp

    async def index_exists(self, index_name: str):
        resp = await self.client.indices.exists(index=index_name)
        return resp

    async def delete_index(self, index_name: str):
        resp = await self.client.indices.exists(index=index_name)
        if not resp:
            print(f"Index {index_name} does not exist. Skipping deletion...")
            return

        resp = await self.client.indices.delete(index=index_name)
        return resp

    async def insert_document(self, index_name: str, id: str, document: dict):
        resp = await self.client.index(index=index_name, document=document, id=id)
        return resp

    async def delete_document(self, index_name: str, id: str):
        resp = await self.client.delete(index=index_name, id=id)
        return resp

    async def search(self, index_name: str, search_query: str):
        resp = await self.client.search(index=index_name, body={"query": {"query_string": {"query": search_query}}})  # type: ignore
        return resp

    async def update_document(self, index_name: str, id: str, document: dict):
        resp = await self.client.index(index=index_name, document=document, id=id)
        return resp

    async def get_date_histogram(self, index_name: str, field: str):
        resp = await self.client.search(index=index_name, size="0", body={"aggs": {"responses_over_time": {"date_histogram": {"field": field, "calendar_interval": "year"}}}})  # type: ignore
        return resp

    async def run_aggregation_query(self, index_name: str, query: dict):
        resp = await self.client.search(index=index_name, size="0", body={"aggs": query})  # type: ignore
        return resp

    async def get_sum_aggregation(self, index_name: str, field: str, field2: str):
        resp = await self.client.search(
            index=index_name,
            size="0",
            body={  # type: ignore
                "aggs": {
                    "responses_over_time": {
                        "date_histogram": {"field": field, "calendar_interval": "year"},
                        "aggs": {"sum_responses": {"sum": {"field": field2}}},
                    }
                }
            },
        )
        return resp

    async def get_word_cloud(self, index_name: str, field: str):
        resp = await self.client.search(
            index=index_name,
            size="0",
            body={  # type: ignore
                "aggs": {
                    "word_frequency": {
                        "terms": {"field": field, "size": 1},
                    }
                }
            },
        )
        return resp


async def test():
    import json
    import os

    es_client = ElasticsearchClient(cloud_id=os.getenv("ELASTIC_CLOUD_ID"), password=os.getenv("ELASTIC_PASSWORD"))
    print(es_client.client)
    index_id = "654fd269-d841-401a-b045-c48d86bfb459"
    resp = await es_client.get_date_histogram(index_id, "account.accountCreatedDate")
    print(json.dumps(resp.body, indent=2))
    index_id = "03e17b34-d9ec-4208-bdc8-d14827ad4e85"
    resp = await es_client.get_word_cloud(index_id, "patientStory.value")
    print(json.dumps(resp.body, indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
