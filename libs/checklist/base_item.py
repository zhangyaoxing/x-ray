from abc import abstractmethod
from enum import Enum
import logging
from bson import json_util
from libs.utils import env

class SEVERITY(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class CATEGORY(Enum):
    SERVER_INFO = "Server Info"
    SECURITY = "Security"
    REPLICA_SET = "Replica Set"

class BaseItem:
    def __init__(self, output_folder: str, config: dict = None):
        self._name = "BaseItem"
        self._description = "Base item for checklist framework. If you see this, it means the item is not properly defined."
        self._category = "Other"
        self._config = config or {}
        self._test_result = []
        self._logger = logging.getLogger(__name__)
        self._output_folder = output_folder

    @abstractmethod
    def test(self):
        pass

    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description
    
    @property
    def category(self):
        return self._category

    @property
    def sample_result(self):
        with open(self.cache_file_name, "r") as f:
            return json_util.loads(f.read())
        
    @sample_result.setter
    def sample_result(self, data):
        with open(self.cache_file_name, "w") as f:
            if env == "development":
                # Pretty print in development mode for easier debugging
                f.write(json_util.dumps(data, indent=4))
            else:
                f.write(json_util.dumps(data))

    @property
    def cache_file_name(self):
        return f"{self._output_folder}/{self._name}.json"