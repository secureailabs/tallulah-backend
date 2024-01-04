import datetime

from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient


class AzureBlobManager:
    def __init__(self, connection_string, container_name):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    async def upload_blob(self, file_name, data):
        async with self.container_client.get_blob_client(blob=file_name) as blob_client:
            await blob_client.upload_blob(data)
            return f"Uploaded {file_name} successfully."

    async def download_blob(self, file_name):
        async with self.container_client.get_blob_client(blob=file_name) as blob_client:
            downloader = await blob_client.download_blob()
            return await downloader.readall()

    async def delete_blob(self, file_name):
        blob_client = self.container_client.get_blob_client(blob=file_name)
        await blob_client.delete_blob()
        return f"Deleted {file_name} successfully."

    def generate_read_sas(self, file_name, expiry_hours=1):
        blob_client = self.container_client.get_blob_client(blob=file_name)
        if not self.blob_service_client.account_name:
            raise Exception("Account name is not set")
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_client.container_name,
            blob_name=file_name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expiry_hours),
        )
        return f"{blob_client.url}?{sas_token}"

    def generate_write_sas(self, file_name, expiry_hours=1):
        blob_client = self.container_client.get_blob_client(blob=file_name)
        if not self.blob_service_client.account_name:
            raise Exception("Account name is not set")
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_client.container_name,
            blob_name=file_name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(write=True),
            expiry=datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expiry_hours),
        )
        return f"{blob_client.url}?{sas_token}"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.blob_service_client.close()
