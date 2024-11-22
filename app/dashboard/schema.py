
import dashboard.types as dashboard_types
import dashboard.inputs as dashboard_inputs
import typing
import strawberry
from dashboard.services.weaviate_service import WeaviateService
from dashboard.services.wordpress_service import WordpressApiService
from dashboard.models import PostSynchronizationProgress
from datetime import datetime
from dashboard.tasks import synchronize_posts
from asgiref.sync import sync_to_async

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
        

    @strawberry.field
    async def post_synchronization_status(self, info:strawberry.Info, task_id:int)->dashboard_types.PostSynchronizationProgressType|None:
        """
        Retrieves the status of a post synchronization task.
        @param task_id: The id of the task.
        """
        try:
            task = await PostSynchronizationProgress.objects.aget(id=task_id)
            return dashboard_types.PostSynchronizationProgressType.from_dict({
                "id": task.id,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "progress": task.progress,
                "status": task.status,
                "message": task.message
            })

        except PostSynchronizationProgress.DoesNotExist:
            return None

    
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
    async def synchronize(self, info:strawberry.Info, modified_date:str)->dashboard_types.PostSynchronizationProgressType|None:
        """
        Synchronize posts from wordpress rest api to Weaviate.
        """
        task = await PostSynchronizationProgress.objects.acreate()
        try:
            modified_date = datetime.fromisoformat(modified_date)
        except ValueError:
            await task.aupdate_progress(PostSynchronizationProgress.STATUS_FAILED, f'Invalid date format. Expected format: YYYY-MM-DDTHH:MM:SS', current_step=-1)
            return dashboard_types.PostSynchronizationProgressType.from_dict({
                "id": task.id,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "progress": task.progress,
                "status": task.status,
                "message": task.message
            })
        
        await task.aupdate_progress(PostSynchronizationProgress.STATUS_PENDING, f'Starting synchronization of posts modified after {modified_date}', current_step=0)
        synchronize_posts.apply_async((modified_date, task.id), countdown=5)
        return dashboard_types.PostSynchronizationProgressType.from_dict({
            "id": task.id,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "progress": task.progress,
            "status": task.status,
            "message": task.message
        })
        

@strawberry.type
class Mutation:

    @strawberry.field
    async def dataset(self)->DatasetMutation:
        return DatasetMutation()
    
    @strawberry.field
    async def posts(self)->PostMutation:
        return PostMutation()

schema = strawberry.Schema(query=Query, mutation=Mutation)