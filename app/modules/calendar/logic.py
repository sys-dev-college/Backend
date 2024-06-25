import uuid

from sqlalchemy import Date, and_, cast, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import joinedload

from app.modules.calendar.models import Calendar, CalendarType
from app.modules.calendar.schemas import CalendarFilter, CalendarIn
from app.modules.users.models import User


async def get_calendar(session: AsyncSession, data: CalendarFilter):
    calendars_instances = await session.scalars(
        select(Calendar)
        .where(
            and_(
                Calendar.user_id == data.user_id,
                cast(Calendar.scheduled, Date) == data.scheduled,
            )
        )
        .order_by(Calendar.scheduled)
        .options(
            joinedload(Calendar.tasks),
            joinedload(Calendar.user)
        )
    )
    calendars_obj = []
    for calendar in calendars_instances.unique():
        calendar.assigner = await session.scalar(
            select(User).where(User.id == calendar.assigner_id)
        )
        calendar.complete = bool(all(task.completed for task in calendar.tasks) is True)
        calendars_obj.append(calendar)

    return calendars_obj


async def get_trainer_calendar(session: AsyncSession, data: CalendarFilter):
    calendars_instances = await session.scalars(
        select(Calendar)
        .join(User, User.id == Calendar.user_id)
        .where(
            and_(
                User.trainer_id == data.user_id,
                cast(Calendar.scheduled, Date) == data.scheduled,
                Calendar.type == CalendarType.EXERCISE,
            )
        )
        .order_by(Calendar.scheduled)
        .options(
            joinedload(Calendar.tasks),
            joinedload(Calendar.user)
        )
    )
    calendars_obj = []
    for calendar in calendars_instances.unique():
        calendar.assigner = await session.scalar(
            select(User).where(User.id == calendar.assigner_id)
        )
        calendar.complete = bool(all(task.completed for task in calendar.tasks) is True)
        calendars_obj.append(calendar)

    return calendars_obj


async def create_calendar_instance(
        session: AsyncSession,
        data: CalendarIn,
        current_user: User,
):
    calendar_instance = Calendar(**data.model_dump())
    session.add(calendar_instance)
    await session.flush()
    calendar_instance.user = await session.scalar(
        select(User)
        .where(User.id == data.user_id)
    )
    calendar_instance.tasks = []
    calendar_instance.assigner = await session.scalar(
            select(User).where(User.id == current_user.id)
        )
    return calendar_instance


async def delete_calendar_logic(session: AsyncSession, calendar_id: uuid.UUID):
    await session.execute(
        delete(Calendar)
        .where(Calendar.id == calendar_id)
    )
