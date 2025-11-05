from datetime import datetime
import hashlib
from libs.utils import *
from bson import json_util

def to_json(obj, indent=None):
    def custom_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        else:
            return json_util.default(o)
    return json.dumps(obj, indent=indent, default=custom_serializer)

def json_hash(data, digest_size=8):
    json_str = to_json(data, indent=None)
    h = hashlib.blake2b(json_str.encode("utf-8"), digest_size=digest_size)
    return h.digest().hex().upper()

MAX_DATA_POINTS = 1024