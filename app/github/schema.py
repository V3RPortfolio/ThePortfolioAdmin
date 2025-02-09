import github.services.github_service as github_service
from github.services.caching_service import GQLCachingService
import github.types as github_types
from github.models import GithubRepository
from authentication.models import RoleType
from authentication.decorators import require_graphql_roles

import typing
import strawberry
import json



@strawberry.type
class Query:
    
    @strawberry.field
    @require_graphql_roles([RoleType.ADMIN])    
    async def issue_counts(self, info:strawberry.Info)->typing.List[github_types.GithubIssueCount]:
        """
        Retrieves the issues from the Github REST API.
        """
        caching_service = GQLCachingService()
        cache_prefix = "issue_counts"
        if caching_service.cache_exists(prefix=cache_prefix, request=info.context.request):
            result = json.loads(caching_service.retrieve(prefix=cache_prefix, request=info.context.request))
            if result:
                return [github_types.GithubIssueCount.from_dict(data) for data in result]

        async with github_service.GithubRestApiService() as service:
            repositories:typing.List[GithubRepository] = service.get_all_repository_names()
            issues = []
            for repository in repositories:
                result = await service.get_issue_count(repository)
                if not result or type(result) is not dict:
                    continue

                issues.append(github_types.GithubIssueCount.from_dict(result))

            if len(issues) > 0:
                caching_service.store(
                    prefix=cache_prefix,
                    value=json.dumps([issue.to_dict() for issue in issues]),
                    request=info.context.request
                )
            return issues
        


schema = strawberry.Schema(query=Query)