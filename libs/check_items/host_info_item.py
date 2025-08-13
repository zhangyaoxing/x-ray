
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from libs.check_items.base_item import BaseItem
from libs.shared import discover_nodes
from libs.utils import red, yellow


class HostInfoItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Host Information"
        self._description = "Collects and reviews host hardware and OS information."

    def _gather_host_info(self, node):
        """
        Gather host information from the given node URI.
        """
        try:
            if "pingLatencySec" in node and node["pingLatencySec"] > 60:
                self._logger.warning(yellow(f"Skip {node['host']} because its last heartbeat is earlier than 60s ago."))
                return None
            client = MongoClient(node["uri"])
            host_info = client.admin.command("hostInfo")
            return host_info
        except Exception as e:
            self._logger.error(red(f"Failed to gather host info from {node['host']}: {str(e)}"))
        return None

    def test(self, *args, **kwargs):
        """
        Main test method to gather host information.
        """
        self._logger.info(f"Gathering host info...")
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)
        host_info_all = {
            "type": nodes["type"],
        }
        if nodes["type"] == "RS":
            self._logger.info(f"Replica Set detected, gathering host info from all members...")
            host_info_all["members"] = {node["host"]: self._gather_host_info(node) for node in nodes["members"]}
        elif nodes["type"] == "SH":
            self._logger.info(f"Sharded Cluster detected, gathering host info from all config/shards members...")
            for k, v in nodes["map"].items():
                host_info_all[k] = {node["host"]: self._gather_host_info(node) for node in v["hosts"]}
            host_info_all["mongos"] = {node["host"]: self._gather_host_info(node) for node in nodes["mongos"]}

            self.sample_result = host_info_all