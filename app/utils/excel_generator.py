import io
from typing import Any, Dict, Iterable, List, Optional, Union

from pyexcelerate.Alignment import Alignment
from pyexcelerate.Border import Border
from pyexcelerate.Borders import Borders
from pyexcelerate.Font import Font
from pyexcelerate.Style import Style
from pyexcelerate.Workbook import Workbook
from pyexcelerate.Worksheet import Worksheet

DATA = Union[
    Iterable[Dict[str, Any]],
    Iterable[Iterable[Any]],
]

HEADERS = Union[
    Dict[str, Any],
    Iterable[str],
]


class ExcelGenerator:
    """Helper for generate sheets in .xlsx format.

    Usage:
        eg = ExcelGenerator()
        eg.new_sheet(
            sheet_name="Users",
            headers=['Name', 'Surname', 'Age'],
            data=[{
                'name':'John',
                'surname': 'Smith',
                'age': 45
            }]
        )
        fp = eg.save()

    This will generate in memory xlsx file with that structure:
        | Name | Surname | Age |
        | John | Smith   | 45  |

    """

    BORDERS = Borders(
        top=Border(style="thin"),
        bottom=Border(style="thin"),
        left=Border(style="thin"),
        right=Border(style="thin"),
    )
    HEADER_CELL_STYLE = Style(
        font=Font(bold=True),
        alignment=Alignment(horizontal="center", vertical="center"),
        size=-1,
        borders=BORDERS,
    )
    COLUMN_STYLE = Style(alignment=Alignment(vertical="center"), size=-1)
    CELL_STYLE = Style(borders=BORDERS)

    def __init__(self):
        self.wb = Workbook()

    def _prepare_data(self, data: DATA) -> List[list]:
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(list(item.values()))
            elif isinstance(item, Iterable):
                result.append(list(item))
            else:
                error_message = f"Incorrect item type: {type(item)} at data ('{item}')"
                raise ValueError(error_message)
        return result

    def new_sheet(self, sheet_name: str, data: DATA, headers: Optional[HEADERS] = None):
        sheet = self.wb.new_sheet(sheet_name)
        if headers:
            self.write_headers(sheet=sheet, headers=headers)
        self.write_data(sheet=sheet, data=data)

    def write_data(self, sheet: Worksheet, data: DATA):
        prepared_data = self._prepare_data(data)

        for row_num, row in enumerate(prepared_data, start=sheet.num_rows + 1):
            for column_num, item in enumerate(row, start=1):
                sheet.set_cell_value(x=row_num, y=column_num, value=item)
                sheet.set_cell_style(x=row_num, y=column_num, value=self.CELL_STYLE)

    def write_headers(self, sheet: Worksheet, headers: HEADERS):
        if isinstance(headers, dict):
            headers = list(headers.keys())

        for column, item in enumerate(headers, start=1):
            sheet.set_cell_value(x=1, y=column, value=item)
            sheet.set_cell_style(x=1, y=column, value=self.HEADER_CELL_STYLE)
            sheet.set_col_style(column, self.COLUMN_STYLE)

    def save(self) -> io.BytesIO:
        fp = io.BytesIO()
        self.wb.save(fp)
        fp.seek(0)
        return fp

    def save_to_file(self, filename: str):
        self.wb.save(filename)
