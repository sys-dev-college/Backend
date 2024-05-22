from fastapi import APIRouter

from app.middlewares.request_processing import RequestProcessingRoute

router = APIRouter(
    tags=["Invites"],
    prefix="/api/invites",
    route_class=RequestProcessingRoute,
)
