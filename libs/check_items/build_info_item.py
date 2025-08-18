from libs.check_items.base_item import BaseItem
from libs.shared import MAX_MONGOS_PING_LATENCY, SEVERITY, discover_nodes, enum_all_nodes, enum_result_items
from libs.utils import *

class BuildInfoItem(BaseItem):
    def __init__(self, output_folder: str, config: dict = None):
        super().__init__(output_folder, config)
        self._name = "Build Info"
        self._description = "Collects & review server build information."

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering server build information...")
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)
        def func_node(set_name, node, **kwargs):
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                return [], None
            client = node["client"]
            raw_result = client.admin.command("buildInfo")
            test_result = []
            eol_version = self._config.get("eol_version", [4, 4, 0])
            running_version = raw_result.get("versionArray", None)
            if running_version[0] < eol_version[0] or \
            (running_version[0] == eol_version[0] and running_version[1] < eol_version[1]):
                test_result.append({
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": "Server Version EOL",
                    "description": f"Server version {running_version} is below EOL version {eol_version}. Consider upgrading to the latest version."
                })
            self.append_test_results(test_result)
            
            return test_result, raw_result

        raw_result = enum_all_nodes(nodes, func_mongos_member=func_node, func_rs_member=func_node, func_shard_member=func_node, func_config_member=func_node)

        self.captured_sample = raw_result

    @property
    def review_result(self):
        result = self.captured_sample
        table = {
            "type": "table",
            "caption": f"Server Build Information",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Version", "type": "string"},
                {"name": "OpenSSL", "type": "string"},
                {"name": "Target Arch", "type": "string"},
                {"name": "Target OS", "type": "string"}
            ],
            "rows": []
        }
        def func_node(name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if raw_result is None:
                table["rows"].append([name, host, "n/a", "n/a", "n/a", "n/a"])
                return
            build_env = raw_result.get("buildEnvironment", {})
            table["rows"].append([name, host, 
                                  raw_result.get("version", ""),
                                  raw_result.get("openssl", {}).get("running", ""),
                                  build_env.get("target_arch", ""),
                                  build_env.get("target_os", "")])
        enum_result_items(result, func_mongos_member=func_node, func_rs_member=func_node, func_shard_member=func_node, func_config_member=func_node)
        
        return {
            "name": self.name,
            "description": self.description,
            "data": [table]
        }