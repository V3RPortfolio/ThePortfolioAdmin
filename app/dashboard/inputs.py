import strawberry
import typing

@strawberry.input
class DatasetPropertyInput:
    name:str
    type:str
    description:typing.Optional[str]
    is_vector:bool
    is_indexed:bool

@strawberry.input
class DatasetInput:
    name:str
    description:typing.Optional[str]
    properties:typing.Optional[typing.List[DatasetPropertyInput]]