import github.services.github_service as github_service
import github.types as github_types
from github.models import GithubRepository

import typing
import strawberry




@strawberry.type
class Query:
    
    @strawberry.field
    async def issue_counts(self)->typing.List[github_types.GithubIssueCount]:
        """
        Retrieves the issues from the Github REST API.
        """
        async with github_service.GithubRestApiService() as service:
            repositories:typing.List[GithubRepository] = service.get_all_repository_names()
            issues = []
            for repository in repositories:
                result = await service.get_issue_count(repository)
                if not result or type(result) is not dict:
                    continue

                issues.append(github_types.GithubIssueCount.from_dict(result))
            return issues
        


schema = strawberry.Schema(query=Query)