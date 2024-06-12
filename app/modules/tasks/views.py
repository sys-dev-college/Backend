import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.tasks.logic import (
    create_task_instance,
    delete_task_logic,
    get_task_instances,
)
from app.modules.tasks.schemas import TaskIn, TaskList, TaskOut
from app.utils.dependencies import get_session
from app.utils.response_helper import DefaultResponse

task_router = APIRouter(
    tags=["Task"],
    prefix="/api/tasks",
    route_class=RequestProcessingRoute,
)


@task_router.post("/")
async def create_task(
        data: TaskIn,
        session: AsyncSession = Depends(get_session),
):
    task_obj = await create_task_instance(
        session=session,
        data=data,
    )
    return TaskOut.model_validate(task_obj)


@task_router.get("/")
async def get_tasks(
        calendar_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
):
    calendars_obj = await get_task_instances(session=session, calendar_id=calendar_id)
    return TaskList.model_validate(calendars_obj)


@task_router.delete("/")
async def delete_task(
        task_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
):
    await delete_task_logic(session=session, task_id=task_id)
    return DefaultResponse(
        success=True,
        message="Task was deleted successfully",
        status_code=200
    )
