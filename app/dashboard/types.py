import typing
import strawberry
from datetime import datetime


@strawberry.type
class Dataset:
    id:str
    name:str
    description:typing.Optional[str]

    @staticmethod
    def to_dict(dataset):
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description
        }
    
    @staticmethod
    def from_dict(data:dict):
        if not data or type(data) is not dict:
            return None

        return Dataset(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", "")
        )


@strawberry.type
class Post:
    id:str
    postId:str
    postTitle:str
    postExcerpt:str
    postContent:str
    postDate:datetime
    postAuthor:str
    postCategories:typing.Optional[str]
    postTags:typing.Optional[str]
    postUrl:typing.Optional[str]

    @staticmethod
    def to_dict(post):
        return {
            "id": post.id,
            "postId": post.postId,
            "postTitle": post.postTitle,
            "postExcerpt": post.postExcerpt,
            "postContent": post.postContent,
            "postDate": post.postDate,
            "postAuthor": post.postAuthor,
            "postCategories": post.postCategories,
            "postTags": post.postTags,
            "postUrl": post.postUrl
        }
    
    @staticmethod
    def from_dict(data:dict):
        if not data or type(data) is not dict:
            return None

        return Post(
            id=data.get("id", ""),
            postId=data.get("postId", ""),
            postTitle=data.get("postTitle", ""),
            postExcerpt=data.get("postExcerpt", ""),
            postContent=data.get("postContent", ""),
            postDate=data.get("postDate", ""),
            postAuthor=data.get("postAuthor", ""),
            postCategories=data.get("postCategories", ""),
            postTags=data.get("postTags", ""),
            postUrl=data.get("postUrl", "")
        )
