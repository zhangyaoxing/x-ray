"""Utility functions and classes for the X-Ray project."""

import importlib
import os
import json
import logging
import pkgutil
import re
import hashlib
from enum import Enum
from inspect import getsourcefile
from os.path import abspath, dirname
from pathlib import Path
from bson import json_util
from libs.version import Version

levels = logging._nameToLevel
level = os.getenv("LOG_LEVEL", "INFO")
env = os.getenv("ENV", "production")
ai_key = os.getenv("OPENAI_API_KEY", "")
if level not in levels:
    level = "INFO"
log_level = levels[level]
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)
logger.info("Using log level: %s", level)


# The script can be started from other working folder. E.g. Invoked by a cron job.
# This function gives you the base path of the script.
# If `filename` is provided then the path include the file. Otherwise it's the folder.
def get_script_path(filename=None):
    import sys

    # Check if running in a PyInstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        script_folder = Path(dirname(abspath(getsourcefile(lambda: 0))))
        base_path = str((script_folder / "..").resolve())

    if filename is None:
        return base_path
    else:
        return str(Path(base_path) / filename)


def _load_config():
    # Use a mutable container to hold cached config to avoid nonlocal assignment warnings.
    config = None

    def func(config_path="config.json"):
        nonlocal config
        if config is None:
            try:
                # First try to load from the path provided by the user
                if os.path.isfile(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    logger.info("Loaded config from user-provided path: %s", config_path)
                    return config

                # Then try to load from the script path
                script_config_path = get_script_path(config_path)
                if os.path.isfile(script_config_path):
                    with open(script_config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    logger.info("Loaded config from script path: %s", script_config_path)
                    return config

                # Finally, try current working directory
                cwd_config_path = os.path.join(os.getcwd(), config_path)
                if os.path.isfile(cwd_config_path):
                    with open(cwd_config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    logger.info("Loaded config from current directory: %s", cwd_config_path)
                    return config

                # If all fails, raise an error
                raise FileNotFoundError(f"Could not find config file: {config_path}")

            except Exception as e:
                logger.error("Failed to load config file: %s", e)
                raise
        return config

    return func


load_config = _load_config()


MAX_CONTENT_WORDS = 3
MORE_CONTENT = "..."


def truncate_content(content: str, delimiter="[ \t]", max_words=MAX_CONTENT_WORDS, more_content=MORE_CONTENT) -> str:
    content = content.strip()
    truncated = re.split(delimiter, content)
    if len(truncated) <= max_words:
        return content
    return " ".join(truncated[:max_words]) + f" {more_content}"


def tooltip_html(full, truncated) -> str:
    html = f'<span class="tooltip" data-tip="{full}">{truncated}</span>'
    return html


def load_classes(package_name="libs.log_analysis.log_items"):
    class_map = {}
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package_name}.{module_name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type):
                class_map[attr] = obj
    logger.debug("Loaded getMongoData analysis classes: %s", list(class_map.keys()))
    return class_map


def format_size(size_bytes, decimal=2):
    """
    Format the size in bytes to a human-readable string.

    Args:
        bytes (int): The size in bytes.
        decimal (int): The number of decimal places to include.

    Returns:
        str: The formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.{decimal}f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.{decimal}f} PB"


def escape_markdown(text):
    """
    Escape markdown special characters.
    """
    ESCAPE_MAP = {"_": "\\_", "*": "\\*", "`": "\\`", "|": "\\|", "<": "&lt;", ">": "&gt;"}
    if not isinstance(text, str):
        text = str(text)
    # Escape underscores, asterisks, backticks, and other special characters
    for key, value in ESCAPE_MAP.items():
        text = text.replace(key, value)
    return text


def format_json_md(json_data, **kwargs):
    """
    Format JSON data as a markdown code block.
    If indent is None or 0, returns a compressed JSON string without line breaks.
    """
    indent = kwargs.get("indent", 2)
    if indent is None or indent == 0:
        kwargs["separators"] = (",", ": ")
        kwargs["indent"] = None
        json_str = to_ejson(json_data, **kwargs)
    else:
        json_str = to_ejson(json_data, **kwargs).replace(" ", "&nbsp;").replace("\n", "<br>")
    return json_str


def to_ejson(obj, **kwargs):
    indent = kwargs.pop("indent", 2)
    separators = kwargs.pop("separators", None)
    cls_maps = [{"class": Enum, "func": lambda o: o.name}, {"class": Version, "func": str}]
    cls_maps.extend(kwargs.pop("cls_maps", []))

    def custom_serializer(o):
        for cls_map in cls_maps:
            cls = cls_map.get("class", None)
            func = cls_map.get("func", None)
            if cls and func and isinstance(o, cls):
                return func(o)
        return json_util.default(o)

    # Must use json.dumps because bson.json_util.dumps has its own serializer behavior,
    # and won't always call our custom_serializer.
    # It only calls when the object is not serializable by default.
    return json.dumps(obj, indent=indent, separators=separators, default=custom_serializer)


def json_hash(data, digest_size=8):
    json_str = to_ejson(data, indent=None)
    h = hashlib.blake2b(json_str.encode("utf-8"), digest_size=digest_size)
    return h.digest().hex().upper()


def color_code(code):
    return f"\x1b[{code}m"


def colorize(code: int, s: str) -> str:
    return f"{color_code(code)}{str(s).replace(color_code(0), color_code(code))}{color_code(0)}"


def green(s: str) -> str:
    return colorize(32, s)


def yellow(s: str) -> str:
    return colorize(33, s)


def red(s: str) -> str:
    return colorize(31, s)


def cyan(s: str) -> str:
    return colorize(36, s)


def magenta(s: str) -> str:
    return colorize(35, s)


def bold(s: str) -> str:
    return colorize(1, s)


def dim(s: str) -> str:
    return colorize(2, s)


def italic(s: str) -> str:
    return colorize(3, s)


def underline(s: str) -> str:
    return colorize(4, s)


def blink(s: str) -> str:
    return colorize(5, s)


def reverse(s: str) -> str:
    return colorize(7, s)


def invisible(s: str) -> str:
    return colorize(8, s)
