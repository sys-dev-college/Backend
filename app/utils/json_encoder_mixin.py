import datetime
import json
from json.encoder import JSONEncoder
from uuid import UUID


class JSONEncoderMixin(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.timedelta):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%d-%m-%Y, %H:%M:%S")
        return json.JSONEncoder.default(self, obj)
