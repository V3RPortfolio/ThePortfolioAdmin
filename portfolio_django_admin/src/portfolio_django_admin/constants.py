import os

# Github configurations
GITHUB_REPOSITORY_OWNER = "zuhairmhtb"
GITHUB_REPOSITORY_FRONTEND = "ThePortfolioFrontend"
GITHUB_REPOSITORY_CMS = "ThePortfolioCMS"
GITHUB_REPOSITORY_INFRASTRUCTURE = "ThePortfolioInfrastructure"
GITHUB_REPOSITORY_ADMIN = "ThePortfolioAdmin"

GITHUB_REPOSITORY_TOKEN = os.getenv("GITHUB_PAT", "")

# Organization Service configurations
JARVIS_GATEWAY_URL = os.getenv("JARVIS_GATEWAY_URL", "http://localhost:8001")
