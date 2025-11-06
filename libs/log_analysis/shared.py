from datetime import datetime
from libs.utils import *


def to_json(obj, indent=None):
    cls_maps = [{"class": datetime, "func": lambda o: o.isoformat()}]
    return to_ejson(obj, indent=indent, cls_maps=cls_maps)


MAX_DATA_POINTS = 1024
