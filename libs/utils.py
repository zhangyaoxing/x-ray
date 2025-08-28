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
    import sys
    
    # Check if running in a PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        script_folder = Path(dirname(abspath(getsourcefile(lambda:0))))
        base_path = str((script_folder / "..").resolve())
        
    if filename == None:
        return base_path
    else:
        return str(Path(base_path) / filename)
    
config = None
def load_config(config_path = "config.json"):
    global config
    if not config:
        try:
            # First try to load from the path provided by the user
            if os.path.isfile(config_path):
                config = json.load(open(config_path))
                logger.info(f"Loaded config from user-provided path: {config_path}")
                return config
                
            # Then try to load from the script path
            script_config_path = get_script_path(config_path)
            if os.path.isfile(script_config_path):
                config = json.load(open(script_config_path))
                logger.info(f"Loaded config from script path: {script_config_path}")
                return config
                
            # Finally, try current working directory
            cwd_config_path = os.path.join(os.getcwd(), config_path)
            if os.path.isfile(cwd_config_path):
                config = json.load(open(cwd_config_path))
                logger.info(f"Loaded config from current directory: {cwd_config_path}")
                return config
                
            # If all fails, raise an error
            raise FileNotFoundError(f"Could not find config file: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise
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