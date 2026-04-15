from celery import shared_task
from notification.dto import PublishUserNotificationDTO
from notification.services.notification_service import create_notification

import asyncio
import logging

logger = logging.getLogger(__name__)


async def publish(dto: PublishUserNotificationDTO):
    await create_notification(dto)

@shared_task(ignore_result=True)
def publish_notification(notification_data: dict):
    notification = PublishUserNotificationDTO(**notification_data)
    logger.info(f"Publishing notification for user_id: {notification.user_id}, title: {notification.title}, description: {notification.description}, image_url: {notification.image_url}, link_url: {notification.link_url}, notification_type: {notification.notification_type}")
    asyncio.run(publish(notification))
    logger.info(f"Notification saved for user_id: {notification.user_id}")