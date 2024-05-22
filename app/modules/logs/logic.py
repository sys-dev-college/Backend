from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.logs.models import Logs
from app.modules.logs.schemas import ReportLog
from app.modules.users.models import User
from app.utils.excel_generator import ExcelGenerator


async def get_logs_obj_by_condition(session: AsyncSession, **kwargs):
    filters = (getattr(Logs, field) == value for field, value in kwargs.items())
    user_log_query = (
        select(Logs)
        # .join(Document, Document.id == Logs.document_id, full=True)
        .options(selectinload(Logs.user), joinedload(Logs.document))
        .where(and_(*filters))
        .order_by(Logs.created_at.desc())
    )

    result = await session.scalars(user_log_query)
    return result.all()


async def build_filter_query(report_data: ReportLog):
    query_filters = []
    if report_data.filters is not None:
        new_data = report_data.filters.model_dump(exclude_unset=True)
        filter_mappings = {
            "user_id": (Logs.user_id,),
            "user_email": (User.email,),
            "action": (Logs.name,),
            # "document": (Document.id,),
        }
        query_filters = [
            filter_mappings[key][0] == value
            for key, value in new_data.items()
            if key in filter_mappings
        ]
    query_filters.append(Logs.room_id == report_data.room_id)
    return query_filters


async def get_log_report_logic(query_filters, session: AsyncSession):
    stmt = (
        select(
            Logs.name.label("type"),
            Logs.created_at.label("timestamp"),
            User.first_name.label("user_name"),
            User.last_name.label("user_last_name"),
            User.email.label("user_email"),
            # Document.name.label("document_name"),
            # Document.size.label("document_size"),
        )
        # .join(Document, Document.id == Logs.document_id, isouter=True)
        .join(User, User.id == Logs.user_id)
        .where(and_(*query_filters))
        .order_by(Logs.created_at.desc())
    )
    result = await session.execute(stmt)
    return result


async def generate_report_excel_file_logic(report_data):
    list_of_data = [dict(row._asdict()) for row in report_data.all()]
    excel_data = []
    for num, i in enumerate(list_of_data, start=1):
        excel_data.append(
            {
                "№": num,
                "Имя пользователя": f"{i['user_name']} {i['user_last_name']}",
                "Email": i["user_email"],
                "Действие": i["type"],
                "Документ": i["document_name"],
                "Дата": i["timestamp"].date().isoformat(),
                "Время": i["timestamp"].time().isoformat(),
                "Размер документа (Кбайт)": i["document_size"],
            }
        )
    excel_file = ExcelGenerator()
    excel_file.new_sheet(
        sheet_name="Result",
        headers=list(excel_data[0].keys()),
        data=excel_data,
    )
    result_file = excel_file.save()
    return result_file
