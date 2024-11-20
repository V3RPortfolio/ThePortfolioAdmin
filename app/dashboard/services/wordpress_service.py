from django.conf import settings
import httpx
import dashboard.types as dashboard_types
import base64
import typing
from datetime import datetime
import asyncio
from bs4 import BeautifulSoup
import re

class PaginatedResponse:
    def __init__(self, data:typing.List[dict], total:int=0, total_pages:int=1, page:int=1, per_page:int=10):
        self.data = data
        self.total = total
        self.total_pages = total_pages
        self.page = page
        self.per_page = per_page

class WordpressApiService:
    def __init__(self):
        self.wordpress_backend = settings.WORDPRESS_BACKEND
        self.wordpress_user = settings.WORDPRESS_USER
        self.wordpress_key = settings.WORDPRESS_KEY
        self.token = base64.b64encode(f"{self.wordpress_user}:{self.wordpress_key}".encode("utf-8"))
        self.endpoints = {
            'post category': 'categories',
            'post': 'posts',
            'author': 'users',
            'tag': 'tags'
        }
        self.categories:dict = {}
        self.authors:dict = {}
        self.tags:dict = {}
        self.http_client:httpx.AsyncClient = None


    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(
            base_url=self.wordpress_backend,
            headers={"Authorization": f"Basic {self.token}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            self.http_client.aclose()


    async def fetch_list(self, endpoint:str, token:str, filters:dict={}, fields:typing.List[str]=[], page:int=1, per_page:int=10)->PaginatedResponse:
        """
        Fetches a list of item from Wordpress Rest API V2
        @param endpoint: str - The endpoint to fetch data from
        @param token: str - The token to use for authentication
        @param filters: dict - The filters to apply to the query
        @param fields: list - The fields to fetch from the query
        @param page: int - The page number to fetch
        @param per_page: int - The number of items to fetch per page
        """
        if not endpoint in self.endpoints:
            return PaginatedResponse([], page=page, per_page=per_page)
        
        headers = { 'Authorization': f"Basic {token}" } if token else {}
        params = {
            "page": page,
            "per_page": per_page
        }
        if filters:
            for key, value in filters.items():
                params[key] = value

        if fields:
            for i in range(len(fields)):
                params[f"_fields[{i}]"] = fields[i]

        result = PaginatedResponse([], page=page, per_page=per_page)
        response = await self.http_client.get(self.endpoints[endpoint], params=params, headers=headers)
        if response.status_code != 200:
            return result

        result.data = response.json()
        if not result.data or type(result.data) != list or len(result.data) == 0:
            result.data = []
            return result

        if response.headers:
            result.total = int(response.headers.get("X-WP-Total", str(len(result.data))))
            result.total_pages = int(response.headers.get("X-WP-TotalPages", "1"))


        return result

    async def fetch_details(self, endpoint:str, token:str, uid:int, fields:typing.List[str]=[])->dict:
        """
        Fetches the details of an item from Wordpress Rest API V2
        @param endpoint: str - The endpoint to fetch data from
        @param token: str - The token to use for authentication
        @param uid: int - The unique identifier of the item
        @param fields: list - The fields to fetch from the query
        """
        if not endpoint in self.endpoints:
            return {}
        headers = { 'Authorization': f"Basic {token}" } if token else {}
        params = {}
        if fields:
            for i in range(len(fields)):
                params[f"_fields[{i}]"] = fields[i]
                
        response = await self.http_client.get(f"{self.endpoints[endpoint]}/{uid}", headers=headers, params=params)
        if response.status_code != 200:
            return {}
        return response.json()
    

    async def retrieve_category_names(self, category_ids:typing.List[int])->typing.List[str]:
        """
        Returns category names for a list of category ids
        @param category_ids: list - The list of category ids
        """
        if not category_ids or len(category_ids) == 0:
            return []
        
        names = []
        for category_id in category_ids:
            if category_id in self.categories:
                names.append(self.categories[category_id]["name"])
                continue

            category = await self.fetch_details('post category', self.token, category_id, fields=["name"])
            if category and "name" in category:
                names.append(category["name"])
                self.categories[category_id] = category

        return names
    
    async def retrieve_author_name(self, author_id:int)->str:
        """
        Returns the author name for an author id
        @param author_id: int - The author id
        """
        if author_id in self.authors:
            return self.authors[author_id]["name"]
        
        author = await self.fetch_details('author', self.token, author_id, fields=["name"])
        if author and "name" in author:
            self.authors[author_id] = author
            return author["name"]
        return ""
    
    async def retrieve_tag_names(self, tag_ids:typing.List[int])->typing.List[str]:
        """
        Returns tag names for a list of tag ids
        @param tag_ids: list - The list of tag ids
        """
        if not tag_ids or len(tag_ids) == 0:
            return []
        
        names = []
        for tag_id in tag_ids:
            if tag_id in self.tags:
                names.append(self.tags[tag_id]["name"])
                continue

            tag = await self.fetch_details('tag', self.token, tag_id, fields=["name"])
            if tag and "name" in tag:
                names.append(tag["name"])
                self.tags[tag_id] = tag

        return names
    

    def clean_html_content(self, html_content:str)->str:
        """
        Cleans HTML content (like content and excerpt). Keeps only the formatted text
        @param html_content: str - The html content
        """
        soup = BeautifulSoup(html_content, 'html.parser')
    
        # Remove all tags except anchor tags and images
        for tag in soup.find_all(True):
            if tag.name != 'a' and tag.name != 'img':
                tag.unwrap()
        
        # Extract the remaining text and anchor tags
        result = soup.get_text()    
        # Replace multiple newlines with one newline
        result = re.sub(r'\n+', '\n', result)
        # Replace multiple spaces with one space
        result = re.sub(r' +', ' ', result)

        return result
    

    async def wordpress_to_post_object(self, post:dict)->dashboard_types.Post:
        """
        Converts a Wordpress Post to a Post Object
        @param post: dict - The Wordpress Post
        """
        if not post or type(post) is not dict:
            return None

        # Fetch the category names
        post_categories = await self.retrieve_category_names(post["categories"])  if post["categories"] else []
        if len(post_categories) > 0:
            post["categories"] = ",".join(post_categories) # categories are comma-separated names

        # Fetch tags
        post_tags = await self.retrieve_tag_names(post["tags"]) if post["tags"] else []
        if len(post_tags) > 0:
            post["tags"] = ",".join(post_tags) # tags are comma-separated names

        # Fetch author
        post["author"] = await self.retrieve_author_name(post["author"]) if post["author"] else ""
        

        # Create post object
        field_mappings = dashboard_types.Post.get_field_mapping()
        mapped_post = {}
        for system_key, wordpress_key in field_mappings.items():

            if wordpress_key in post:
                if wordpress_key == "excerpt" or wordpress_key == "content" or wordpress_key == "title": # The html content of content and excerpt exists inside rendered
                    mapped_post[system_key] = post[wordpress_key]["rendered"] if post[wordpress_key]["rendered"] else str(post[wordpress_key])
                    mapped_post[system_key] = self.clean_html_content(mapped_post[system_key])
                elif wordpress_key == "date_gmt": # convert it to datetime from iso string
                    try:
                        mapped_post[system_key] = datetime.fromisoformat(post[wordpress_key])
                    except:
                        mapped_post[system_key] = datetime.utcnow()
                        
                else:
                    mapped_post[system_key] = post[wordpress_key]

        return dashboard_types.Post.from_dict(mapped_post)
        
        
    async def get_posts(self, modified_date:datetime)->typing.List[dashboard_types.Post]:
        """
        Retrieves all posts from wordpress rest api that were modified after a given date
        """
        fields = [value for _, value in dashboard_types.Post.get_field_mapping().items()]
        current_page = 1
        per_page = 10
        endpoint = "post"
        filters = {
            "orderby": "date",
            "order": "asc",
            "modified_after": modified_date.isoformat()
        }

        posts = await self.fetch_list(endpoint, token=self.token, page=current_page, per_page=per_page, fields=fields, filters=filters)
        total_pages = posts.total_pages

        requests =[]
        if total_pages > 1:
            current_page += 1
            while current_page <= total_pages:
                requests.append(self.fetch_list(endpoint, token=self.token, page=current_page, per_page=per_page, fields=fields, filters=filters))
                current_page += 1

        # Wait till all requests are executed and responses are returned
        response = await asyncio.gather(*requests)
        for r in response:
            if len(r.data) > 0:
                posts.data.extend(r.data)


        post_object_requests = []
        for post in posts.data:
            post_object_requests.append(self.wordpress_to_post_object(post))

        # Wait till all posts have been converted to post objects
        post_objects = await asyncio.gather(*post_object_requests)

        return post_objects

        