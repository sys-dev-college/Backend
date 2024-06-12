import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.request_processing import RequestProcessingRoute

# from app.modules.documents.models import Document
from app.modules.logs import logic
from app.modules.logs.schemas import FilterLog, GetLogsList, ReportLog
from app.utils.dependencies import get_session

log_router = APIRouter(
    tags=["Logs"],
    prefix="/api/logs",
    route_class=RequestProcessingRoute,
)


@log_router.get("/")
async def get_room_logs(
    filter_query: FilterLog = Depends(),
    session: AsyncSession = Depends(get_session),
):
    logs_obj = await logic.get_logs_obj_by_condition(
        session, **filter_query.model_dump(exclude_none=True)
    )
    return GetLogsList.model_validate(logs_obj)


@log_router.get("/user/")
async def get_user_logs(
    user_id: uuid.UUID,
    room_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> GetLogsList:
    logs_obj = await logic.get_logs_obj_by_condition(session, user_id=user_id, room_id=room_id)

    return GetLogsList.model_validate(logs_obj)


@log_router.get("/document/")
async def get_logs_by_document_id(
    session: AsyncSession = Depends(get_session), document_id: uuid.UUID = Query()
):
    # document_id_exists = await Document.get_document_by_conditions(
    #     session, Document.id == document_id
    # )
    # if document_id_exists is None:
    #     return DefaultResponse(success=False, message="No such document", status_code=404)

    logs_obj = await logic.get_logs_obj_by_condition(session, document_id=document_id)

    return GetLogsList.model_validate(logs_obj)


@log_router.post("/report/")
async def get_report_of_log_view(
    report_filter: ReportLog,
    session: AsyncSession = Depends(get_session),
):
    query_filters = await logic.build_filter_query(report_filter)
    queryset = await logic.get_log_report_logic(query_filters, session)
    result = await logic.generate_report_excel_file_logic(queryset)
    return StreamingResponse(
        result,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Report.xlsx"},
    )
