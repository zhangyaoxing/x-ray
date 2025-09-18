from libs.utils import *
from bson import json_util

def to_json(obj, indent=None):
    return json_util.dumps(obj, indent=indent)