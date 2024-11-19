
import dashboard.types as dashboard_types
import typing
import strawberry
import json

@strawberry.type
class Query:

    @strawberry.field
    async def datasets(self, info:strawberry.Info)->typing.List[dashboard_types.Dataset]:
        """
        Retrieves all collections from Weaviate.
        """
        result = []
        
        return result
    

schema = strawberry.Schema(query=Query)