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
