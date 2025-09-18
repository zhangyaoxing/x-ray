import datetime
import os
from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import json_hash
import math

class ClientMetaItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(ClientMetaItem, self).__init__(output_folder, config)
        self._cache = {}
        self.name = "Client Metadata"
        self.description = "Visualize client metadata."
        self._cache = {}

    def analyze(self, log_line):
        msg = log_line.get("msg", "")
        if msg != "client metadata":
            return
        attr = log_line.get("attr", {})
        ip = attr["remote"].split(":")[0]
        doc = attr["doc"]
        doc_hash = json_hash(doc)
        self._cache[doc_hash] = {
            "doc": doc
        }
        if "ips" not in self._cache[doc_hash]:
            self._cache[doc_hash]["ips"] = []
        self._cache[doc_hash]["ips"].append(ip)
