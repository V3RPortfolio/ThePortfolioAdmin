
import dashboard.types as dashboard_types
import dashboard.inputs as dashboard_inputs
import typing
import strawberry
from dashboard.services.weaviate_service import WeaviateService
import json


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
class Mutation:

    @strawberry.field
    async def dataset(self)->DatasetMutation:
        return DatasetMutation()

schema = strawberry.Schema(query=Query, mutation=Mutation)