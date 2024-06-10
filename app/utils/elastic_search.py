from elasticsearch import AsyncElasticsearch


class ElasticsearchClient:
    _instance = None

    def __new__(cls, cloud_endpoint=None, password=None):
        if cls._instance is None:
            if cloud_endpoint is None or password is None:
                raise Exception("cloud_id and password must be provided")
            cls._instance = super(ElasticsearchClient, cls).__new__(cls)
            cls.client = AsyncElasticsearch(hosts=cloud_endpoint, basic_auth=("elastic", password))
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

    async def search(self, index_name: str, search_query: str, size: int = 10, skip: int = 0):
        resp = await self.client.search(
            index=index_name, size=size, from_=skip, query={"query_string": {"query": search_query}}
        )
        return resp

    async def update_document(self, index_name: str, id: str, document: dict):
        resp = await self.client.index(index=index_name, document=document, id=id)
        return resp

    async def run_aggregation_query(self, index_name: str, query: dict):
        resp = await self.client.search(index=index_name, size=0, body=query)  # type: ignore
        return resp
