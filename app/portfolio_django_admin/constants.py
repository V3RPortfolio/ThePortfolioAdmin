import os

# Github configurations
GITHUB_REPOSITORY_OWNER = "zuhairmhtb"
GITHUB_REPOSITORY_FRONTEND = "ThePortfolioFrontend"
GITHUB_REPOSITORY_CMS = "ThePortfolioCMS"
GITHUB_REPOSITORY_INFRASTRUCTURE = "ThePortfolioInfrastructure"
GITHUB_REPOSITORY_ADMIN = "ThePortfolioAdmin"

GITHUB_REPOSITORY_TOKEN = os.getenv("GITHUB_PAT", "")

# Weaviate configurations
WEAVIATE_POST_COLLECTION = "Post"
WEAVIATE_MAX_WORD_PER_POST=100