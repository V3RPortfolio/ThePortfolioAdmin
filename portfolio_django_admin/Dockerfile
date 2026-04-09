FROM astral/uv:python3.12-bookworm-slim

# Configure uv to use the system environment
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_SYSTEM_PYTHON="true"
ENV UV_PYTHON_PREFERENCE="only-system"



# Set working directory
WORKDIR /usr/local/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . ./app/
WORKDIR /usr/local/app/
RUN uv sync

WORKDIR /usr/local/app/src/

# Default command runs FastAPI app with Uvicorn
CMD ["uv", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "portfolio_django_admin.asgi:application"]