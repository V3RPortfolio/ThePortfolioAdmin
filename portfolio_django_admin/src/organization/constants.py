from enum import Enum
from uuid import UUID


class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
    DELETED = "deleted"

class PaymentCurrency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CREDITS = "credits"

class UserInvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class DeviceType(Enum):
    DESKTOP = "Desktop"
class DeviceDataType(Enum):
    USER_ACCESS = "user_access"
    CPU_AND_MEMORY_USAGE = "cpu_and_memory_usage"
    IO_DEVICE_USAGE = "io_device_usage"
    

CACHE_KEY_PREFIX = "org_role_cache"
CACHE_TIMEOUT = 86400  # 24 hours


def build_cache_key(organization_id: UUID, username: str) -> str:
    return f"{CACHE_KEY_PREFIX}__{organization_id}__{username}"