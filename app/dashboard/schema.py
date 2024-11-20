
import dashboard.types as dashboard_types
import dashboard.inputs as dashboard_inputs
import typing
import strawberry
from dashboard.services.weaviate_service import WeaviateService
from dashboard.services.wordpress_service import WordpressApiService
from datetime import datetime


@strawberry.type
class Query:
    @strawberry.field
    async def datasets(self, info:strawberry.Info, name:typing.Optional[str]=None)->typing.List[dashboard_types.Dataset]:
        """
        Retrieves all collections from Weaviate.
        """
        result = []
        async with WeaviateService() as service:
            if not name or len(name) == 0:
                result = await service.get_collections()
            else:
                result = [await service.view_collection(name=name)]
        return result
    
    @strawberry.field
    async def posts(self, info:strawberry.Info, modified_date:str)->typing.List[dashboard_types.Post]:
        """
        Retrieves all posts from wordpress rest api that were modified after a given date
        """
        async with WordpressApiService() as service:
            return await service.get_posts(modified_date=datetime.fromisoformat(modified_date))

    
@strawberry.type
class DatasetMutation:

    @strawberry.mutation
    async def delete(self, info:strawberry.Info, name:str)->dashboard_types.Dataset|None:
        """
        Deletes a collection from Weaviate.
        """
        async with WeaviateService() as service:
            return await service.delete_collection(name=name)
        
    @strawberry.mutation
    async def add(self, info:strawberry.Info, dataset:dashboard_inputs.DatasetInput)->dashboard_types.Dataset|None:
        """
        Adds a collection to Weaviate.
        """
        async with WeaviateService() as service:
            return await service.add_collection(dataset=dashboard_types.Dataset(
                name=dataset.name,
                id=dataset.name,
                description=dataset.description,
                properties=[
                    dashboard_types.DatasetProperty(
                        name=prop.name,
                        id=prop.name,
                        type=prop.type,
                        description=prop.description,
                        is_indexed=prop.is_indexed,
                        is_vector=prop.is_vector
                    ) for prop in dataset.properties
                ]
            ))
        

@strawberry.type
class PostMutation:

    @strawberry.mutation
    async def synchronize(self, info:strawberry.Info, modified_date:str)->typing.List[dashboard_types.Post]:
        """
        Synchronize posts from wordpress rest api to Weaviate.
        """
        try:
            modified_date = datetime.fromisoformat(modified_date)
        except ValueError:
            return []
        
        async with WordpressApiService() as service:
            posts = await service.get_posts(modified_date=modified_date)
            if len(posts) == 0:
                return []
            
            async with WeaviateService() as weaviate_service:
                return await weaviate_service.synchronize_posts(posts)
        return []

@strawberry.type
class Mutation:

    @strawberry.field
    async def dataset(self)->DatasetMutation:
        return DatasetMutation()
    
    @strawberry.field
    async def posts(self)->PostMutation:
        return PostMutation()

schema = strawberry.Schema(query=Query, mutation=Mutation)