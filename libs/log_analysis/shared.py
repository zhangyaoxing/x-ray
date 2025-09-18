from datetime import datetime
import hashlib
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

def json_hash(data):
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    h = hashlib.blake2b(json_str.encode("utf-8"), digest_size=8)
    return h.digest().hex()