import os

# Github configurations
GITHUB_REPOSITORY_OWNER = "zuhairmhtb"
GITHUB_REPOSITORY_FRONTEND = "ThePortfolioFrontend"
GITHUB_REPOSITORY_CMS = "ThePortfolioCMS"
GITHUB_REPOSITORY_INFRASTRUCTURE = "ThePortfolioInfrastructure"
GITHUB_REPOSITORY_ADMIN = "ThePortfolioAdmin"

GITHUB_REPOSITORY_TOKEN = os.getenv("GITHUB_PAT", "")

# Organization Service configurations
ORGANIZATION_SERVICE_URL = os.getenv("ORGANIZATION_SERVICE_URL", "http://localhost:8001")
