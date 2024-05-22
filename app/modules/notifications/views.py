from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationList, NotificationOut, NotificationUpdate
from app.modules.users.models import User
from app.utils.dependencies import get_current_user, get_session
from app.utils.response_helper import DefaultResponse

notification_router = APIRouter(
    tags=["Notifications"],
    prefix="/api/notifications",
    route_class=RequestProcessingRoute,
)


@notification_router.get("/")
async def get_notifications(
    session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)
) -> NotificationList:
    notifications_query = (
        select(Notification)
        .join(User, User.id == Notification.user_id)
        .where(Notification.user_id == current_user.id)
        .options(selectinload(Notification.user))
        .order_by(Notification.created_at.desc())
    )
    notifications = await session.scalars(notifications_query)

    return NotificationList.model_validate(notifications)


@notification_router.put("/")
async def update_notification(
    data: NotificationUpdate, session: AsyncSession = Depends(get_session)
):
    notification_query = (
        update(Notification)
        .where(Notification.id == data.notification_id)
        .values(status=data.status)
        .returning(Notification)
        .options(selectinload(Notification.user))
    )
    notification_instance: Notification = await session.scalar(notification_query)
    if not notification_instance:
        return DefaultResponse(
            status_code=400,
            success=False,
            message="Notification doesn't exist",
        )

    return NotificationOut.model_validate(notification_instance)
