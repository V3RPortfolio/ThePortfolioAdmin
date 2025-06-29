import os

# Github configurations
GITHUB_REPOSITORY_OWNER = "zuhairmhtb"
GITHUB_REPOSITORY_FRONTEND = "ThePortfolioFrontend"
GITHUB_REPOSITORY_CMS = "ThePortfolioCMS"
GITHUB_REPOSITORY_INFRASTRUCTURE = "ThePortfolioInfrastructure"
GITHUB_REPOSITORY_ADMIN = "ThePortfolioAdmin"

GITHUB_REPOSITORY_TOKEN = os.getenv("GITHUB_PAT", "")

DEVICE_TOKEN_HEADER = "X-Device-Token"
OPENAPI_DEVICE_EXTRA = {
    "parameters": [
        {
            "name": "X-Device-Token",
            "in": "header",
            "required": True
        }
    ]
}