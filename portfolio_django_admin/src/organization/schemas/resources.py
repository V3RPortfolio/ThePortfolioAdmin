from pydantic import BaseModel, Field
from typing import Optional, List

class ManageResourceDto(BaseModel):
    """
    Data Transfer Object for managing organization information.
    """
    organization_id: str = Field(..., description="ID of the organization")
    name: Optional[str] = Field(None, description="Name of the organization")
    is_active: Optional[bool] = Field(None, description="Whether the organization is active")


class ResourceIndexDto(BaseModel):
    name: str = Field(..., description="Name of the index")
    major_version: int = Field(..., description="Major version number of the index schema. It should be incremented when there are breaking changes in the schema which requires reindexing of data.")
    minor_version: int = Field(..., description="Minor version number of the index schema. It should be incremented when there are non-breaking changes in the schema which does not require reindexing of data.")
    patch_version: int = Field(..., description="Patch version number of the index schema. It should be incremented when there are minor changes in the schema such as adding new properties which does not require reindexing of data.")

    last_attempted_provisioned_at: str = Field(..., description="Timestamp when the index was last provisioned")
    provision_status: Optional[str] = Field(..., description="Provision status of the index. It can be one of 'pending', 'in_progress', 'completed', 'failed'")


class ResourceDto(BaseModel):
    """
    Data Transfer Object for organization response.
    """
    organization_id: str = Field(..., description="ID of the organization")
    name: str = Field(..., description="Name of the organization")
    is_active: bool = Field(..., description="Whether the organization is active")
    indices: List[ResourceIndexDto] = Field(default_factory=list, description="List of indices associated with the organization")