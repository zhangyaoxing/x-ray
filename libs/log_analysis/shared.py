from datetime import datetime
import hashlib
from libs.utils import *

def to_json(obj, indent=None):
    cls_maps = [{
        "class": datetime,
        "func": lambda o: o.isoformat()
    }]
    return to_json_internal(obj, indent=indent, cls_maps=cls_maps)

def json_hash(data, digest_size=8):
    json_str = to_json(data, indent=None)
    h = hashlib.blake2b(json_str.encode("utf-8"), digest_size=digest_size)
    return h.digest().hex().upper()

MAX_DATA_POINTS = 1024