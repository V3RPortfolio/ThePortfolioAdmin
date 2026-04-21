from typing import Optional
import httpx
import portfolio_django_admin.constants as constants
from organization.schemas.resources import ManageResourceDto, ResourceDto


class ResourceService:
    """
    This service communicates with Organization Service via Backend API.
    The openapi.json file is available in docs/ folder.
    It uses httpx based async communication to update and retrieve organization specific data in the organization service.
    It forwards user's JWT bearer token received by this application to the organization service for authentication and authorization.
    """

    def __init__(self, jwt_token: str):
        self.base_url = constants.ORGANIZATION_SERVICE_URL
        self.jwt_token = jwt_token
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ResourceService":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.jwt_token}"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def get_organization(self, organization_id: str) -> ResourceDto:
        """
        Retrieve organization information.
        GET /organization/{organization_id}/v1
        """
        response = await self._client.get(f"/organization/{organization_id}/v1")
        response.raise_for_status()
        return ResourceDto(**response.json())

    async def create_organization(self, payload: ManageResourceDto) -> ResourceDto:
        """
        Create a new organization.
        POST /organization/v1
        """
        response = await self._client.post(
            "/organization/v1",
            json=payload.model_dump(),
        )
        response.raise_for_status()
        return ResourceDto(**response.json())

    async def update_organization(self, payload: ManageResourceDto) -> ResourceDto:
        """
        Update an existing organization.
        PUT /organization/v1
        """
        response = await self._client.put(
            "/organization/v1",
            json=payload.model_dump(),
        )
        response.raise_for_status()
        return ResourceDto(**response.json())

    async def delete_organization(self, organization_id: str) -> ResourceDto:
        """
        Delete an organization.
        DELETE /organization/{organization_id}/v1
        """
        response = await self._client.delete(f"/organization/{organization_id}/v1")
        response.raise_for_status()
        return ResourceDto(**response.json())

    # ------------------------------------------------------------------
    # Provisioning
    # ------------------------------------------------------------------

    async def provision_organization_index(self, organization_id: str) -> dict:
        """
        Provision the search index for an organization.
        POST /organization/{organization_id}/provision/v1
        """
        response = await self._client.post(
            f"/organization/{organization_id}/provision/v1"
        )
        response.raise_for_status()
        return response.json()

    async def deprovision_organization_index(self, organization_id: str) -> dict:
        """
        Deprovision the search index for an organization.
        POST /organization/{organization_id}/deprovision/v1
        """
        response = await self._client.post(
            f"/organization/{organization_id}/deprovision/v1"
        )
        response.raise_for_status()
        return response.json()
