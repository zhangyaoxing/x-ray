from datetime import datetime
from libs.utils import *
from bson import json_util

def to_ejson(obj, indent=None):
    return json_util.dumps(obj, indent=indent)

def to_json(obj, indent=None):
    def custom_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        else:
            return json._json_default(o)
    return json.dumps(obj, indent=indent, default=custom_serializer)