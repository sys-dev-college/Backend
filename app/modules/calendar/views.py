import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.calendar.logic import create_calendar_instance, get_calendar, delete_calendar_logic
from app.modules.calendar.schemas import CalendarFilter, CalendarIn, CalendarList, CalendarOut
from app.modules.users.models import User
from app.utils.dependencies import get_current_user, get_session
from app.utils.response_helper import DefaultResponse

calendar_router = APIRouter(
    tags=["Calendar"],
    prefix="/api/calendars",
    route_class=RequestProcessingRoute,
)


@calendar_router.post("/")
async def create_calendar(
    data: CalendarIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    calendar_obj = await create_calendar_instance(
        session=session,
        data=data,
        current_user=current_user,
    )
    return CalendarOut.model_validate(calendar_obj)


@calendar_router.post("/tasks/")
async def get_calendars(
    data: CalendarFilter,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not data.user_id:
        data.user_id = current_user.id
    calendars_obj = await get_calendar(session=session, data=data)
    return CalendarList.model_validate(calendars_obj)


@calendar_router.delete("/")
async def delete_calendar(
        calendar_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
):
    await delete_calendar_logic(session=session, calendar_id=calendar_id)
    return DefaultResponse(
        success=True,
        message="Calendar was deleted successfully",
        status_code=200
    )
