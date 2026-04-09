from typing import List
import httpx
import portfolio_django_admin.constants as constants
import github.models as models


class GithubRestApiService:
    """
    This service retrieves and extracts data from the Github REST API.
    """
    def __init__(self):
        self.github_api_url = "https://api.github.com/graphql"
        self.github_token = constants.GITHUB_REPOSITORY_TOKEN
        self.github_owner = constants.GITHUB_REPOSITORY_OWNER
        self.http_client:httpx.AsyncClient = None


    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(
            base_url=self.github_api_url,
            headers={"Authorization": f"token {self.github_token}"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            self.http_client.aclose()


    def get_all_repository_names(self)->List[models.GithubRepository]:
        """
        Retrieves the repositories from the Github REST API.
        Note: Move it to the database later.
        """
        return [
            models.GithubRepository(
                name=constants.GITHUB_REPOSITORY_FRONTEND,
                title="The Angular Frontend",
                description="The Angular Frontend for the system",
                url="https://github.com/zuhairmhtb/ThePortfolioFrontend.git"
            ),
            models.GithubRepository(
                name=constants.GITHUB_REPOSITORY_CMS,
                title="The WordPress Backend",
                description="The WordPress CMS for the system",
                url="https://github.com/zuhairmhtb/ThePortfolioCMS.git"
            ),
            models.GithubRepository(
                name=constants.GITHUB_REPOSITORY_INFRASTRUCTURE,
                title="The Infrastructure",
                description="The Infrastructure for the system",
                url="https://github.com/zuhairmhtb/ThePortfolioInfrastructure.git"
            ),
            models.GithubRepository(
                name=constants.GITHUB_REPOSITORY_ADMIN,
                title="The Django Admin",
                description="The Django Admin for the system",
                url="https://github.com/zuhairmhtb/ThePortfolioAdmin.git"
            )
        ]
    

    async def get_issue_count(self, repository:models.GithubRepository)->dict:
        query = f"""query ($owner: String = "{self.github_owner}", $name: String = "{repository.name}") {{
  repository(owner: $owner, name: $name) {{
    all:issues {{
      totalCount
    }}
    closed:issues(states:CLOSED) {{
      totalCount
    }}
    open:issues(states:OPEN) {{
      totalCount
    }}
  }}
}}"""
        response = await self.http_client.post(url=self.github_api_url, json={"query": query})
        result = response.json()
        issue_info = {}
        if "data" in result and "repository" in result["data"] and type(result["data"]["repository"]) is dict:
            issue_info['all'] = result["data"]["repository"]["all"]["totalCount"]
            issue_info['closed'] = result["data"]["repository"]["closed"]["totalCount"]
            issue_info['open'] = result["data"]["repository"]["open"]["totalCount"]
            issue_info["repository"] = repository.name
            issue_info["title"] = repository.title
            issue_info["description"] = repository.description
            issue_info["icon"] = repository.icon
            issue_info["url"] = repository.url

            
        return issue_info
        


    


    