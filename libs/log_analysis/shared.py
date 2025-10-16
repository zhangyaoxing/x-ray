from datetime import datetime
import hashlib
from libs.utils import *
from bson import json_util

# TODO: some of these functions should be merged with shared.py in healthcheck, and moved to libs/utils.py
def to_ejson(obj, indent=None):
    return json_util.dumps(obj, indent=indent)

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

def format_size(bytes, decimal=2):
    """
    Format the size in bytes to a human-readable string.

    Args:
        bytes (int): The size in bytes.
        decimal (int): The number of decimal places to include.

    Returns:
        str: The formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024:
            return f"{bytes:.{decimal}f} {unit}"
        bytes /= 1024
    return f"{bytes:.{decimal}f} PB"

def escape_markdown(text):
    """
    Escape markdown special characters.
    """
    if not isinstance(text, str):
        text = str(text)
    # Escape underscores, asterisks, backticks, and other special characters
    return text.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('|', '\\|').replace('<', '&lt;').replace('>', '&gt;')

def format_json_md(json_data, indent=2):
    """
    Format JSON data as a markdown code block.
    If indent is None or 0, returns a compressed JSON string without line breaks.
    """
    if indent is None or indent == 0:
        json_str = json_util.dumps(json_data, separators=(',', ': '))
    else:
        json_str = json_util.dumps(json_data, indent=indent).replace("\n", "<br />")
    return json_str

def format_json_md(json_data, indent=2):
    """
    Format JSON data as a markdown code block.
    If indent is None or 0, returns a compressed JSON string without line breaks.
    """
    if indent is None or indent == 0:
        json_str = json_util.dumps(json_data, separators=(',', ': '))
    else:
        json_str = json_util.dumps(json_data, indent=indent).replace("\n", "<br />")
    return json_str

MAX_DATA_POINTS = 32
AI_MODEL = "gpt-5"