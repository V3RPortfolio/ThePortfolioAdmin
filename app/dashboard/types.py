from __future__ import annotations
import typing
import strawberry
from datetime import datetime
from weaviate.classes.config import DataType
from abc import ABC, abstractmethod

@strawberry.type
class DatasetProperty:

    TEXT_TYPE = "text"
    NUMBER_TYPE = "number"
    INTEGER_TYPE = "integer"
    DATE_TYPE = "date"
    BOOLEAN_TYPE = "boolean"
    GEO_COORDINATES_TYPE = "geoCoordinates"
    PHONE_NUMBER_TYPE = "phoneNumber"
    UUID_TYPE = "uuid"
    BLOB_TYPE = "blob"
    OBJECT_TYPE = "object"

    id:str
    name:str
    type:str
    description:typing.Optional[str]
    is_vector:bool
    is_indexed:bool

    @staticmethod
    def to_dict(dataset_field:DatasetProperty)->dict:
        return {
            "id": dataset_field.name,
            "name": dataset_field.name,
            "type": dataset_field.type,
            "description": dataset_field.description,
            "is_vector": dataset_field.is_vector,
            "is_indexed": dataset_field.is_indexed
        }
    
    @staticmethod
    def from_dict(data:dict)->DatasetProperty:
        if not data or type(data) is not dict:
            return None

        return DatasetProperty(
            id=data.get("name", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            is_vector=data.get("is_vector", False),
            is_indexed=data.get("is_indexed", False)
        )
    
    @staticmethod
    def to_weaviate_property(propertyName:str)->typing.Type[DataType]:
        if propertyName == DatasetProperty.TEXT_TYPE:
            return DataType.TEXT
        elif propertyName == DatasetProperty.NUMBER_TYPE:
            return DataType.NUMBER
        elif propertyName == DatasetProperty.INTEGER_TYPE:
            return DataType.INT
        elif propertyName == DatasetProperty.DATE_TYPE:
            return DataType.DATE
        elif propertyName == DatasetProperty.BOOLEAN_TYPE:
            return DataType.BOOL
        elif propertyName == DatasetProperty.GEO_COORDINATES_TYPE:
            return DataType.GEO_COORDINATES
        elif propertyName == DatasetProperty.PHONE_NUMBER_TYPE:
            return DataType.PHONE_NUMBER
        elif propertyName == DatasetProperty.UUID_TYPE:
            return DataType.UUID
        elif propertyName == DatasetProperty.BLOB_TYPE:
            return DataType.BLOB
        elif propertyName == DatasetProperty.OBJECT_TYPE:
            return DataType.OBJECT
        else:
            return DataType.TEXT
        
    @staticmethod
    def from_weaviate_property(propertyType:DataType)->str:
        if propertyType == DataType.TEXT:
            return DatasetProperty.TEXT_TYPE
        elif propertyType == DataType.NUMBER:
            return DatasetProperty.NUMBER_TYPE
        elif propertyType == DataType.INT:
            return DatasetProperty.INTEGER_TYPE
        elif propertyType == DataType.DATE:
            return DatasetProperty.DATE_TYPE
        elif propertyType == DataType.BOOL:
            return DatasetProperty.BOOLEAN_TYPE
        elif propertyType == DataType.GEO_COORDINATES:
            return DatasetProperty.GEO_COORDINATES_TYPE
        elif propertyType == DataType.PHONE_NUMBER:
            return DatasetProperty.PHONE_NUMBER_TYPE
        elif propertyType == DataType.UUID:
            return DatasetProperty.UUID_TYPE
        elif propertyType == DataType.BLOB:
            return DatasetProperty.BLOB_TYPE
        elif propertyType == DataType.OBJECT:
            return DatasetProperty.OBJECT_TYPE
        else:
            return DatasetProperty.TEXT_TYPE

@strawberry.type
class Dataset:
    id:str
    name:str
    description:typing.Optional[str]
    properties:typing.Optional[typing.List[DatasetProperty]]

    @staticmethod
    def to_dict(dataset:Dataset)->dict:
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "properties": [DatasetProperty.to_dict(prop) for prop in dataset.properties] if dataset.properties else []
        }
    
    @staticmethod
    def from_dict(data:dict)->typing.Type[Dataset]:
        if not data or type(data) is not dict:
            return None

        return Dataset(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            properties=[DatasetProperty.from_dict(prop) for prop in data.get("properties", [])]
        )


class WeaviateCollection(ABC):

    @staticmethod
    @abstractmethod
    def from_dict(data:dict)->typing.Type[typing.Any]:
        pass

    @staticmethod
    @abstractmethod
    def to_dict(data:typing.Any)->dict:
        pass

    @abstractmethod
    def get_embedding(self)->typing.List[float]:
        pass

    @staticmethod
    @abstractmethod
    def get_field_mapping()->dict:
        pass
    

@strawberry.type
class Post(WeaviateCollection):
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
    
    @staticmethod
    def get_field_mapping()->dict:
        return {
            'postId': 'id',
            'postTitle': 'title',
            'postExcerpt': 'excerpt',
            'postContent': 'content',
            'postDate': 'date_gmt',
            'postAuthor': 'author',
            'postCategories': 'categories',
            'postTags': 'tags',
            'postUrl': 'link'
        }
    
    def get_embedding(self):
        return []
    
