
from pymongo import MongoClient
from libs.check_items.base_item import BaseItem
from libs.shared import *


class ServerStatusItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Server Status Information"
        self._description = "Collects and reviews server status metrics."

    def _check_connections(self, server_status):
        """
        Check the connections metrics.
        """
        test_result = []
        host = server_status.get("host", "unknown")
        connections = server_status.get("connections", {})
        used_connection_ratio = self._config.get("used_connection_ratio", 0.8)
        available = connections.get("available", 0)
        current = connections.get("current", 0)
        total = available + current
        if current / total > used_connection_ratio:
            test_result.append({
                "host": host,
                "severity": SEVERITY.HIGH,
                "title": "High Connection Usage",
                "description": f"Current connections (`{current}`) exceed `{used_connection_ratio * 100:.2f}%` of total connections (`{total}`)."
            })
            
        return test_result, connections

    def _check_query_targeting(self, server_status):
        """
        Check query targeting metrics.
        """
        test_result = []
        host = server_status.get("host", "unknown")
        query_executor = server_status["metrics"].get("queryExecutor", {})
        document = server_status["metrics"].get("document", {})
        scanned_returned = (query_executor["scanned"] / document["returned"]) if document["returned"] > 0 else 0
        scanned_obj_returned = (query_executor["scannedObjects"] / document["returned"]) if document["returned"] > 0 else 0
        query_targeting = self._config.get("query_targeting", {})
        query_targeting_obj = self._config.get("query_targeting_obj", {})
        if scanned_returned > query_targeting:
            test_result.append({
                "host": host,
                "severity": SEVERITY.HIGH,
                "title": "Poor Query Targeting",
                "description": f"Scanned/Returned ratio `{scanned_returned:.2f}` exceeds the threshold `{query_targeting}`."
            })
        if scanned_obj_returned > query_targeting_obj:
            test_result.append({
                "host": host,
                "severity": SEVERITY.HIGH,
                "title": "Poor Query Targeting",
                "description": f"Scanned Objects/Returned ratio `{scanned_obj_returned:.2f}` exceeds the threshold `{query_targeting_obj}`."
            })
            
        return test_result, {
            "scanned/returned": scanned_returned,
            "scanned_obj/returned": scanned_obj_returned
        }

    def test(self, *args, **kwargs):
        """
        Run the server status test.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        def func_all_members(set_name, node, **kwargs):
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                return [], None
            client = node["client"]
            server_status = client.admin.command("serverStatus")
            test_result1, raw_result1 = self._check_connections(server_status)
            test_result2, raw_result2 = self._check_query_targeting(server_status) if set_name != "mongos" else ([], {})
            test_result = test_result1 + test_result2
            self.append_test_results(test_result)
            raw_result = {
                "connections": raw_result1,
                "query_targeting": raw_result2,
                "server_status": server_status
            }
            return test_result, raw_result

        nodes = discover_nodes(client, parsed_uri)
        result = enum_all_nodes(nodes, func_mongos_member=func_all_members, 
                                func_rs_member=func_all_members, func_shard_member=func_all_members, 
                                func_config_member=func_all_members)
        self.captured_sample = result
        
    @property
    def review_result(self):
        result = self.captured_sample
        data = []
        conn_table = {
            "type": "table",
            "caption": f"Connections",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Current", "type": "decimal"},
                {"name": "Available", "type": "decimal"},
                {"name": "Active", "type": "decimal"},
                {"name": "Created", "type": "decimal"}
            ],
            "rows": []
        }
        qt_table = {
            "type": "table",
            "caption": f"Query Targeting",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Scanned / Returned", "type": "decimal"},
                {"name": "Scanned Objects / Returned", "type": "decimal"},
            ],
            "rows": []
        }
        data.append(conn_table)
        data.append(qt_table)
        def func_all_members(set_name, node, **kwargs):
            raw_result = node["rawResult"]
            host = node["host"]
            if raw_result is None:
                return
            connections = raw_result.get("connections", {})
            query_targeting = raw_result.get("query_targeting", {})
            conn_table["rows"].append([
                escape_markdown(set_name),
                host,
                connections.get("current", 0),
                connections.get("available", 0),
                connections.get("active", 0),
                connections.get("created", 0)
            ])
            qt_table["rows"].append([
                escape_markdown(set_name),
                host,
                f"{query_targeting.get('scanned/returned', 0):.2f}",
                f"{query_targeting.get('scanned_objects/returned', 0):.2f}"
            ])
        enum_result_items(result, func_mongos_member=func_all_members, func_rs_member=func_all_members, 
                          func_shard_member=func_all_members, func_config_member=func_all_members)

        return {
            "name": self.name,
            "description": self.description,
            "data": data
        }
