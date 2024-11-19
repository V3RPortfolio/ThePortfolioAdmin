from django.conf import settings
import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.classes.config import Property, DataType, Configure, VectorDistances



from typing import List, Optional, Type

import dashboard.types as dashboard_types

class WeaviateService:
    def __init__(self):
        self.weaviate_host = settings.WEAVIATE_HOST
        self.weaviate_port = settings.WEAVIATE_PORT
        self.weaviate_scheme = settings.WEAVIATE_SCHEME
        self.weaviate_grpc_port = settings.WEAVIATE_GRPC_PORT
        self.weaviate_timeout = settings.WEAVIATE_TIMEOUT
        self.weaviate_token = settings.WEAVIATE_TOKEN
        self.weaviate_user = settings.WEAVIATE_USER

        self.client = self._get_async_client()

    
    def _get_async_client(self):
        """
        Rerturns an WeaviateAsyncClient object
        """
        connection_params = ConnectionParams.from_params(
            http_host=self.weaviate_host,
            http_port=self.weaviate_port,
            http_secure=self.weaviate_scheme == "https",
            grpc_host=self.weaviate_host,
            grpc_port=self.weaviate_grpc_port,
            grpc_secure=self.weaviate_scheme == "https"
        )
        auth_secret = Auth.api_key(self.weaviate_token)
        additional_config = AdditionalConfig(
            timeout=Timeout(init=30, query=60, insert=120),  # Values in seconds
        )
        client = weaviate.WeaviateAsyncClient(
            connection_params=connection_params,
            auth_client_secret=auth_secret,
            additional_config=additional_config,
            skip_init_checks=True
        )
        return client
    
    async def __aenter__(self):
        if self.client and not self.client.is_connected():
            await self.client.connect()

        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.client and self.client.is_connected():
            await self.client.close()
        return False
    

    def _collection_to_dataset(self, collection:weaviate.collections.Collection)->dashboard_types.Dataset:
        dataset = dashboard_types.Dataset(
            id=collection.name,
            name=collection.name,
            description=collection.description,
            properties=[]
        )
        if collection.properties:
            for prop in collection.properties:
                dataset.properties.append(
                    dashboard_types.DatasetProperty(
                        id=prop.name,
                        name=prop.name,
                        type=dashboard_types.DatasetProperty.from_weaviate_property(prop.data_type),
                        description=prop.description,
                        is_indexed=prop.index_filterable,
                        is_vector=prop.vectorizer != None
                    )
                )
        return dataset
    

    async def get_collections(self)->List[dashboard_types.Dataset]:
        """
        Retrieves all collections from Weaviate.
        """
        result = []        
        try:
            collections = await self.client.collections.list_all()
            if not collections:
                return result
            for key, collection in collections.items():
                result.append(self._collection_to_dataset(collection))
        except Exception as e:
            print(f"Error retrieving collections: {e}")
        return result
    
    async def view_collection(self, name:str)->Optional[dashboard_types.Dataset]:
        if not name or len(name) == 0:
            return None
        
        try:
            collection = self.client.collections.get(name)
            if not collection or not await collection.exists():
                return None
            return self._collection_to_dataset(await collection.config.get())
        except Exception as e:
            print(f"Error retrieving collection: {e}")
        return None
        
    

    async def add_collection(self, dataset:dashboard_types.Dataset)->Optional[dashboard_types.Dataset]:
        if not dataset:
            return None
        
        try:
            properties = []
            if dataset.properties and len(dataset.properties) > 0:
                for prop in dataset.properties:
                    properties.append(Property(
                        name=prop.name,
                        description=prop.description,
                        data_type=dashboard_types.DatasetProperty.to_weaviate_property(prop.type),
                        index_filterable=prop.is_indexed,
                        index_searchable=prop.is_indexed  and prop.type == dashboard_types.DatasetProperty.TEXT_TYPE,
                        skip_vectorization=True, # Do not vectorize any property. The vectorization will occur externally
                    ))

            await self.client.collections.create(
                name=dataset.name,
                description=dataset.description,
                vectorizer_config=Configure.Vectorizer.none(), # Do not vectorize any property. The vectorization will occur externally
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                ),
                properties=properties

            )
            print(f"Collection '{dataset.name}' created successfully.")
            return dataset
        except weaviate.exceptions.SchemaValidationException as e:
            print(f"Error creating collection: {e}")

        return None
    
    async def delete_collection(self, name:str)->dashboard_types.Dataset:
        if not name or len(name) == 0:
            return None
        
        try:
            collection = self.client.collections.get(name)
            if not collection or not await collection.exists():
                return None
            await self.client.collections.delete(name)
            print(f"Collection '{name}' deleted successfully.")
            return dashboard_types.Dataset(id=name, name=name, description=None, properties=None)
        except Exception as e:
            print(f"Error deleting collection: {e}")
        return None