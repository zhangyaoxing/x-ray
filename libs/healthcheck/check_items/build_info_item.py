"""Build Info Check Item Module. Used to check MongoDB server build information."""

from libs.healthcheck.check_items.base_item import BaseItem
from libs.healthcheck.shared import MAX_MONGOS_PING_LATENCY, SEVERITY, discover_nodes, enum_all_nodes, enum_result_items
from libs.utils import yellow
from libs.version import Version


class BuildInfoItem(BaseItem):
    def __init__(self, output_folder: str, config: dict = None):
        super().__init__(output_folder, config)
        self._name = "Build Information"
        self._description = "Collects & review server build information.\n\n"
        self._description += "- Whether the server is running a supported version.\n"

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)

        def func_node(set_name, node, **kwargs):
            host = node["host"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(
                        f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            client = node["client"]
            raw_result = client.admin.command("buildInfo")
            test_result = []
            eol_version = Version(self._config.get("eol_version", [4, 4, 0]))
            running_version = Version(raw_result.get("versionArray", None))
            if running_version < eol_version:
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.HIGH,
                        "title": "Server Version EOL",
                        "description": f"Server version {running_version} is below EOL version {eol_version}. Consider upgrading to the latest version.",
                    }
                )
            self.append_test_results(test_result)
            node["version"] = running_version

            return test_result, raw_result

        raw_result = enum_all_nodes(
            nodes,
            func_mongos_member=func_node,
            func_rs_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )

        self.captured_sample = raw_result

    @property
    def review_result(self):
        result = self.captured_sample
        table = {
            "type": "table",
            "caption": "Server Build Information",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Version", "type": "string"},
                {"name": "OpenSSL", "type": "string"},
                {"name": "Target Arch", "type": "string"},
                {"name": "Target OS", "type": "string"},
            ],
            "rows": [],
        }
        versions = {}

        def func_node(name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if raw_result is None:
                table["rows"].append([name, host, "n/a", "n/a", "n/a", "n/a"])
                versions["n/a"] = versions.get("n/a", 0) + 1
                return
            build_env = raw_result.get("buildEnvironment", {})
            v = raw_result.get("version", "")
            versions[v] = versions.get(v, 0) + 1
            table["rows"].append(
                [
                    name,
                    host,
                    v,
                    raw_result.get("openssl", {}).get("running", ""),
                    build_env.get("target_arch", ""),
                    build_env.get("target_os", ""),
                ]
            )

        enum_result_items(
            result,
            func_mongos_member=func_node,
            func_rs_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )
        version_pie = {"type": "chart", "data": versions}

        return {"name": self.name, "description": self.description, "data": [table, version_pie]}
