import httpx
import portfolio_django_admin.constants as constants
class GithubRestApiService:
    """
    This service retrieves and extracts data from the Github REST API.
    """
    def __init__(self):
        self.github_api_url = "https://api.github.com"
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


    def get_all_repository_names(self)->str:
        """
        Retrieves the repositories from the Github REST API.
        """
        return [
            constants.GITHUB_REPOSITORY_FRONTEND,
            constants.GITHUB_REPOSITORY_CMS,
            constants.GITHUB_REPOSITORY_INFRASTRUCTURE,
            constants.GITHUB_REPOSITORY_ADMIN
        ]

    async def get_completed_pull_requests(self, repository_name:str):
        """
        Retrieves the completed pull requests from the Github REST API.
        @param repository_name: The name of the repository.
        """
        response = await self.http_client.get(
            f"/repos/{self.github_owner}/{repository_name}/pulls?state=closed"
        )
        result = response.json()
        print(result)
        return result
        


    


    