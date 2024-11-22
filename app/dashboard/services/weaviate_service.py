from django.conf import settings
import portfolio_django_admin.constants as constants
import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from weaviate.classes.query import Filter
import re
from dashboard.models import PostSynchronizationProgress


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
        self.max_words_per_post = constants.WEAVIATE_MAX_WORD_PER_POST
        self.weaviate_post_collection = constants.WEAVIATE_POST_COLLECTION

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
    
    def _create_chunks_for_post(self, content:str)->List[str]:
        """
        Splits a post content into multiple chunks maintaining a sequence
        @param content: The content of the post
        """
        result = []
        current_char_index = 0
        last_sentence_ended_at = -1
        last_chunk_ended_at = 0
        current_word_count = 0
        
        while current_char_index < len(content) + 1:
            current_char = content[current_char_index] if current_char_index < len(content) else ''
            
            if bool(re.match(r'\s', current_char)): # Increase word count if a whitespace occurs
                current_word_count += 1
            elif current_char == '.': # Store where the last sentence
                last_sentence_ended_at = current_char_index

            # If the max word limit has been reached
            if current_char_index == len(content): # This is the last iteration. So add the entire chunk
                result.append(content[last_chunk_ended_at:current_char_index])
                break
                
            elif current_word_count >= self.max_words_per_post: # The maximum word count has been reached
                if last_chunk_ended_at == last_sentence_ended_at: # Probably the chunk contains code -- Parse code separately later
                    last_sentence_ended_at = current_char_index
                result.append(content[last_chunk_ended_at:last_sentence_ended_at] + ".") # Update the chunk      
                    
                current_word_count = 0 # Reset the word count
                last_chunk_ended_at = last_sentence_ended_at # The next chunk will start from where the current chunk was made
                current_char_index = last_sentence_ended_at + 1 # Go back to where the last chunk ended
            else:          
                current_char_index += 1
        return result
    

    async def synchronize_posts(self, posts:List[dashboard_types.Post], task:PostSynchronizationProgress=None, current_step:int=0)->List[dict]:
        """
        Updates or adds the posts in weaviate
        1. Extract all the post ids
        2. Update all posts in the weaviate collection that matches the post ID and mark it as deleted
        3. Split each post into multiple chunks with sequence number and add them to weaviate.
        4. Fetch all posts from weaviate that are marked as deleted and delete them
        @param posts: List of posts to be synchronized
        @param task: The task object to update the progress
        @param current_step: The current step of the task
        """
        if not posts or len(posts) == 0:
            await task.aupdate_progress(PostSynchronizationProgress.STATUS_COMPLETED, f'No posts found to synchronize', current_step=-1)
            return
        
        try:
            collection = self.client.collections.get(self.weaviate_post_collection)
            if not collection or not await collection.exists():
                return []

            # Update all posts in the weaviate collection that matches the post ID and mark it as deleted
            unique_post_ids = set([post.postId for post in posts])    
            stale_post_ids = []
            await task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, f'Fetching stale posts from the database', current_step=current_step)
            current_step += 1
            for post_id in unique_post_ids:
                existing_posts = await collection.query.fetch_objects(
                    filters=Filter.by_property("postId").equal(str(post_id)),
                )
                stale_post_ids.extend([existing_post.uuid for existing_post in existing_posts.objects])

            stale_post_ids = list(set(stale_post_ids))
            # Split each post into multiple chunks with sequence number and add them to weaviate.
            for i in range(len(posts)):
                post = posts[i]
                await task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, f'Splitting post content into multiple chunks and updating the database. {i} out of {len(posts)} completed.', current_step=current_step)
                chunks = self._create_chunks_for_post(post.postContent)
                post_properties = dashboard_types.Post.to_dict(post)
                del post_properties["id"]
                for index, chunk in enumerate(chunks):
                    post_properties["postContent"] = chunk
                    post_properties["postSequence"] = index + 1
                    post_properties["isDeleted"] = False
                    
                    try:
                        await collection.data.insert(
                            properties=post_properties,
                            vector=dashboard_types.Post.from_dict(post_properties).get_embedding()
                        )
                    except Exception as e:
                        print(f"Error inserting chunk {index} of post {post.postId}")
                        print(e)
                        
            current_step += 1
            await task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, f'Deleting stale posts', current_step=current_step)
            current_step += 1
            # Fetch all posts from weaviate that are marked as deleted and delete them
            await collection.data.delete_many(
                where=Filter.any_of([Filter.by_id().equal(i) for i in stale_post_ids])
            )

            result = []
            await task.aupdate_progress(PostSynchronizationProgress.STATUS_IN_PROGRESS, f'Fetching new posts', current_step=current_step)
            for post_id in unique_post_ids:
                existing_posts = await collection.query.fetch_objects(
                    filters=Filter.by_property("postId").equal(str(post_id)),
                    return_properties=["postId"]
                )
                result.append(existing_posts)
            return result

            
        except Exception as e:
            print(f"Error updating posts: {e}")
            await task.aupdate_progress(PostSynchronizationProgress.STATUS_FAILED, str(e), current_step=current_step)
            return []