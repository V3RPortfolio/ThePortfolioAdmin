from typing import Optional
from pydantic import BaseModel, Field



class PublishUserNotificationDTO(BaseModel):
    user_id: int = Field(..., description="ID of the user to receive the notification")
    title: str = Field(..., description="Title of the notification")
    description: Optional[str] = Field(None, description="Message content of the notification")
    image_url: Optional[str] = Field(None, description="URL of the image to be displayed in the notification")
    link_url: Optional[str] = Field(None, description="URL to navigate when the notification is clicked")
    notification_type: Optional[str] = Field(None, description="Type of the notification, e.g. 'info', 'warning', 'error'")