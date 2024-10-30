import typing
import strawberry
from datetime import datetime



def convert_to_datetime(datetime_str):
  """
  Converts a datetime string in the format '2024-10-28T10:37:57Z' to a datetime object.

  Args:
    datetime_str: The datetime string to convert.

  Returns:
    A datetime object representing the input string.
  """
  try:
    # The 'Z' indicates UTC time. We remove it and add '+00:00' to explicitly specify the timezone
    datetime_str = datetime_str[:-1] + '+00:00'  
    datetime_object = datetime.fromisoformat(datetime_str)
    return datetime_object
  except ValueError:
    print("Invalid datetime string format. Please use 'YYYY-MM-DDTHH:MM:SSZ'")
    return None

DateTime = strawberry.scalar(
    datetime, 
    parse_value=lambda dt: dt.isoformat() + 'Z',
    serialize=lambda dt: convert_to_datetime(dt)
)

@strawberry.type
class GithubUser:
    id:float
    login:str
    avatar_url:typing.Optional[str]

    @staticmethod
    def from_dict(data:dict):
        if not data or type(data) is not dict:
            return None

        return GithubUser(
            id=data.get("id", 0),
            login=data.get("login", ""),
            avatar_url=data.get("avatar_url", "")
        )
    
@strawberry.type
class GithubIssuePullRequest:
    url:str
    html_url:typing.Optional[str]
    diff_url:typing.Optional[str]
    patch_url:typing.Optional[str]
    merged_at:typing.Optional[DateTime]

    @staticmethod
    def from_dict(data:dict):
        if not data or type(data) is not dict:
            return None

        return GithubIssuePullRequest(
            url=data.get("url", ""),
            html_url=data.get("html_url", ""),
            diff_url=data.get("diff_url", ""),
            patch_url=data.get("patch_url", ""),
            merged_at=data.get("merged_at", "")
        )

@strawberry.type
class GithubIssue:
    url: str
    repository_url: str
    id: float
    title:str
    user:typing.Optional["GithubUser"]
    state:typing.Optional[str]
    locked:typing.Optional[bool]
    assignee:typing.Optional["GithubUser"]
    created_at:typing.Optional[DateTime]
    updated_at:typing.Optional[DateTime]
    closed_at:typing.Optional[DateTime]
    author_association:typing.Optional[str]
    draft:typing.Optional[bool]
    pull_request:typing.Optional["GithubIssuePullRequest"]
    body:typing.Optional[str]

    @staticmethod
    def from_dict(data:dict):
        if not data or type(data) is not dict:
            return None

        return GithubIssue(
            url=data.get("url", ""),
            repository_url=data.get("repository_url", ""),
            id=data.get("id", 0),
            title=data.get("title", ""),
            user=GithubUser.from_dict(data.get("user", {})),
            state=data.get("state", ""),
            locked=data.get("locked", False),
            assignee=GithubUser.from_dict(data.get("assignee", {})),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            closed_at=data.get("closed_at", ""),
            author_association=data.get("author_association", ""),
            draft=data.get("draft", False),
            pull_request=GithubIssuePullRequest.from_dict(data.get("pull_request", {})),
            body=data.get("body", "")
        )

@strawberry.type
class GithubIssueCount:
    repository:str
    url: str
    all:int
    closed:int
    open:int
    title:typing.Optional[str]
    description:typing.Optional[str]
    icon:typing.Optional[str]

    @staticmethod
    def from_dict(data:dict):
        if not data or type(data) is not dict:
            return None

        return GithubIssueCount(
            repository=data.get("repository", ""),
            all=data.get("all", 0),
            closed=data.get("closed", 0),
            open=data.get("open", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            url=data.get("url", "")
        )