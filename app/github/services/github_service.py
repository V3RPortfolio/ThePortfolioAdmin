import httpx
import portfolio_django_admin.constants as constants
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
    

    async def get_issue_count(self, repository_name:str)->dict:
        query = f"""query ($owner: String = "{self.github_owner}", $name: String = "{repository_name}") {{
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
            issue_info["repository"] = repository_name
            
        return issue_info
        


    


    