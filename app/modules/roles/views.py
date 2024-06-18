import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute
from app.modules.roles import logic
from app.utils.dependencies import get_session

role_router = APIRouter(
    tags=["Roles"],
    prefix="/api/roles",
    route_class=RequestProcessingRoute,
)


@role_router.get("/")
async def get_all_roles(
    session: AsyncSession = Depends(get_session),
):
    result = await logic.get_all_roles(session)
    return result


@role_router.get("/{role_id}/")
async def get_role_by_id(
    role_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await logic.get_role_by_id(session=session, role_id=role_id)
    return result
