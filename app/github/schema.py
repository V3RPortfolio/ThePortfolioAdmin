import github.services.github_service as github_service

import typing
import strawberry


@strawberry.type
class Book:
    title: str
    author: str


@strawberry.type
class Query:
    books: typing.List[Book]


async def get_books():
    async with github_service.GithubRestApiService() as service:
        result = await service.get_completed_pull_requests("portfolio_admin_experience_django")
        print(result)
    return [
        Book(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
        ),
    ]


@strawberry.type
class Query:
    books: typing.List[Book] = strawberry.field(resolver=get_books)


schema = strawberry.Schema(query=Query)