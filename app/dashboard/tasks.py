from celery import shared_task
from dashboard.services.weaviate_service import WeaviateService
from dashboard.services.wordpress_service import WordpressApiService
from datetime import datetime
import asyncio
from dashboard.models import PostSynchronizationProgress



@shared_task
def synchronize_posts(modified_date:datetime, task_id:int):
    async def synchronize(modified_date:datetime, task_id:int):
        task = None
        try:
            task = await PostSynchronizationProgress.objects.aget(id=task_id)
            task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, 'Synchronization started', current_step=1)

            async with WordpressApiService() as service:
                await task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, 'Fetching posts from Wordpress', current_step=2)
                posts = await service.get_posts(modified_date=modified_date)

                if len(posts) == 0:
                    task.update_progress(PostSynchronizationProgress.STATUS_COMPLETED, 'No new posts to synchronize', current_step=-1)
                    return
                    
                
                async with WeaviateService() as weaviate_service:
                    await task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, f'Updating the database with {len(posts)} new posts', current_step=3)

                    posts = await weaviate_service.synchronize_posts(posts, task=task, current_step=4)

                    await task.aupdate_progress(PostSynchronizationProgress.STATUS_COMPLETED, f'Successfully synchronized {len(posts)} posts', current_step=-1)
                    return
                

        except Exception as e:
            if task:
                task.aupdate_progress(PostSynchronizationProgress.STATUS_FAILED, f'Unable to complete synchronization. {str(e)[:50]}', current_step=-1)
            return

    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(synchronize(modified_date, task_id))
    loop.close()
    return result