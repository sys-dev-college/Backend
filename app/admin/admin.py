from sqladmin import ModelView

from app.modules.calendar.models import Calendar
from app.modules.logs.models import Logs
from app.modules.roles.models import Role
from app.modules.tasks.models import Task
from app.modules.users.models import User, UserParam


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.first_name, User.last_name]


class LogAdmin(ModelView, model=Logs):
    column_list = [Logs.id, Logs.name, Logs.created_at]


class CalendarAdmin(ModelView, model=Calendar):
    column_list = [Calendar.id, Calendar.title, Calendar.scheduled]


class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.name, Task.calendar_id, Task.completed]


class RoleAdmin(ModelView, model=Role):
    column_list = [Role.id, Role.name]


class UserParamAdmin(ModelView, model=UserParam):
    column_list = [UserParam.id, UserParam.user_id, UserParam.name, UserParam.created_at, UserParam.amount]

