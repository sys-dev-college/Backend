import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import joinedload

from app.modules.calendar.models import Calendar, Task
from app.modules.tasks.schemas import TaskIn


async def get_task_instances(session: AsyncSession, calendar_id: uuid.UUID):
    task_instances = await session.scalars(
        select(Task)
        .where(Task.calendar_id == calendar_id,)
        .options(joinedload(Task.calendar))
    )

    return task_instances


async def create_task_instance(
        session: AsyncSession,
        data: TaskIn,
):
    task_instance = Task(**data.model_dump())
    session.add(task_instance)
    await session.commit()
    await session.refresh(task_instance)
    task_instance.calendar = await session.scalar(
        select(Calendar)
        .where(Calendar.id == data.calendar_id)
    )
    return task_instance


async def delete_task_logic(session: AsyncSession, task_id: uuid.UUID):
    await session.execute(
        delete(Task)
        .where(Task.id == task_id)
    )
