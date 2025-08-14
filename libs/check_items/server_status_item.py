
from pymongo import MongoClient
from libs.check_items.base_item import BaseItem
from libs.shared import *


class ServerStatusItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Server Status Information"
        self._description = "Collects and reviews server status metrics."

    def _gather_server_status(self, client):
        """
        Gather server status metrics.
        """
        try:
            server_status = client.admin.command("serverStatus")
            return server_status
        except Exception as e:
            self._logger.warning(f"Failed to gather server status: {str(e)}")
            return None

    def _check_connections(self, server_status):
        """
        Check the connections metrics.
        """
        host = server_status.get("host", "unknown")
        connections = server_status.get("connections", {})
        used_connection_ratio = self._config.get("used_connection_ratio", 0.8)
        available = connections.get("available", 0)
        current = connections.get("current", 0)
        total = available + current
        if current / total > used_connection_ratio:
            self.append_item_result(
                host,
                SEVERITY.HIGH,
                "High Connection Usage",
                f"Current connections (`{current}`) exceed `{used_connection_ratio * 100:.2f}%` of total connections (`{total}`)."
            )
    def _check_query_targeting(self, server_status):
        """
        Check query targeting metrics.
        """
        host = server_status.get("host", "unknown")
        query_executor = server_status["metrics"].get("queryExecutor", {})
        document = server_status["metrics"].get("document", {})
        scanned_returned = (query_executor["scanned"] / document["returned"]) if document["returned"] > 0 else 0
        scanned_obj_returned = (query_executor["scannedObjects"] / document["returned"]) if document["returned"] > 0 else 0
        query_targeting = self._config.get("query_targeting", {})
        query_targeting_obj = self._config.get("query_targeting_obj", {})
        if scanned_returned > query_targeting:
            self.append_item_result(
                host,
                SEVERITY.HIGH,
                "Poor Query Targeting",
                f"Scanned/Returned ratio `{scanned_returned:.2f}` exceeds the threshold `{query_targeting}`."
            )
        if scanned_obj_returned > query_targeting_obj:
            self.append_item_result(
                host,
                SEVERITY.HIGH,
                "Poor Query Targeting",
                f"Scanned Objects/Returned ratio `{scanned_obj_returned:.2f}` exceeds the threshold `{query_targeting_obj}`."
            )

    def test(self, *args, **kwargs):
        """
        Run the server status test.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)
        all_status = {
            "mongos": [],
            "map": {},
        }
        # Gather mongos server status
        for node in nodes["mongos"]:
            uri = node["uri"]
            if node.get("pingLatencySec", 0) > MAX_MONGOS_PING_LATENCY:
                continue
            c = MongoClient(uri, serverSelectionTimeoutMS=5000)
            status = self._gather_server_status(c)
            all_status["mongos"].append(status)
            self._check_connections(status)

        # Gather shard and config server status
        for shard, shard_info in nodes["map"].items():
            all_status["map"][shard] = []
            for node in shard_info["members"]:
                uri = node["uri"]
                c = MongoClient(uri, serverSelectionTimeoutMS=5000)
                status = self._gather_server_status(c)
                all_status["map"][shard].append(status)
                self._check_connections(status)
                self._check_query_targeting(status)

        self.captured_sample = all_status