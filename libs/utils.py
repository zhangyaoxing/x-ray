import os
import json
import logging
from inspect import getsourcefile
from os.path import abspath, dirname
from pathlib import Path

levels = logging._nameToLevel
level = os.getenv("LOG_LEVEL", "INFO")
env = os.getenv("ENV", "production")
if (level not in levels):
    level = "INFO"
log_level = levels[level]
logging.basicConfig(level = log_level)
logger = logging.getLogger(__name__)
logger.info(f"Using log level: {level}")

# The script can be started from other working folder. E.g. Invoked by a cron job.
# This function gives you the base path of the script.
# If `filename` is provided then the path include the file. Otherwise it's the folder.
def get_script_path(filename = None):
    script_folder = Path(dirname(abspath(getsourcefile(lambda:0))))
    if filename == None:
        return str((script_folder / "..").resolve())
    else:
        return str((script_folder / ".." / filename).resolve())
    
config = None
def load_config(config_path = "config.json"):
    global config
    if not config:
        config_path = get_script_path(config_path)
        config = json.load(open(config_path))
    return config

def color_code(code): return f"\x1b[{code}m"
def colorize(code: int, s: str) -> str: return f"{color_code(code)}{str(s).replace(color_code(0), color_code(code))}{color_code(0)}"
def green(s: str) -> str: return colorize(32, s)
def yellow(s: str) -> str: return colorize(33, s)
def red(s: str) -> str: return colorize(31, s)
def cyan(s: str) -> str: return colorize(36, s)
def magenta(s: str) -> str: return colorize(35, s)
def bold(s: str) -> str: return colorize(1, s)
def dim(s: str) -> str: return colorize(2, s)
def italic(s: str) -> str: return colorize(3, s)
def underline(s: str) -> str: return colorize(4, s)
def blink(s: str) -> str: return colorize(5, s)
def reverse(s: str) -> str: return colorize(7, s)
def invisible(s: str) -> str: return colorize(8, s)