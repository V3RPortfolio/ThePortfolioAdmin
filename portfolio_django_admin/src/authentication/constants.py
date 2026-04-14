from enum import Enum


class RoleType(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# Organization Specific constants
class OrganizationRoleType(str, Enum):
    ADMIN = "admin"
    OWNER = "owner"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"

ORG_ADMIN_ROLES = [OrganizationRoleType.OWNER.value, OrganizationRoleType.ADMIN.value]
ORG_MANAGEMENT_ROLES = [
    OrganizationRoleType.OWNER.value,
    OrganizationRoleType.ADMIN.value,
    OrganizationRoleType.MANAGER.value,
]
VALID_ROLES = [role.value for role in OrganizationRoleType]
OWNER_ASSIGNABLE_ROLES = [
    OrganizationRoleType.MANAGER.value,
    OrganizationRoleType.EDITOR.value,
    OrganizationRoleType.VIEWER.value,
]
MANAGER_ASSIGNABLE_ROLES = [
    OrganizationRoleType.EDITOR.value,
    OrganizationRoleType.VIEWER.value,
]