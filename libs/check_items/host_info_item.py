
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from libs.check_items.base_item import BaseItem
from libs.shared import MAX_MONGOS_PING_LATENCY, discover_nodes, enum_all_nodes, enum_result_items, format_size
from libs.utils import red, yellow


class HostInfoItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Host Information"
        self._description = "Collects and reviews host hardware and OS information.  \n"
        self._description += "*This item is to gather information. No test is performed.*\n\n"

    def test(self, *args, **kwargs):
        """
        Main test method to gather host information.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)

        def func_single(name, node, **kwargs):
            client = node["client"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(yellow(f"Skip {node['host']} because it has been irresponsive for {node['pingLatencySec'] / 60} minutes."))
                return None, None
            host_info = client.admin.command("hostInfo")
            return None, host_info
        result = enum_all_nodes(nodes,
                                    func_rs_member=func_single,
                                    func_mongos_member=func_single,
                                    func_shard_member=func_single,
                                    func_config_member=func_single)

        self.captured_sample = result

    @property
    def review_result(self):
        """
        Review the gathered host information.
        """
        result = self.captured_sample
        data = []

        def func_component(name, node, **kwargs):
            members = node["members"]
            table = {
                "type": "table",
                "caption": f"Hardware & OS Information - `{name}`",
                "columns": [
                    {"name": "Host", "type": "string"},
                    {"name": "CPU Family", "type": "string"},
                    {"name": "CPU Cores", "type": "string"},
                    {"name": "Memory", "type": "string"},
                    {"name": "OS", "type": "string"},
                    {"name": "NUMA", "type": "boolean"},
                ],
                "rows": []
            }
            data.append(table)
            for m in members:
                info = m.get("rawResult", None)
                if info is None:
                    table["rows"].append([m["host"], "N/A", "N/A", "N/A", "N/A", "N/A"])
                    continue
                system = info["system"]
                os = info["os"]
                extra = info["extra"]
                table["rows"].append([
                    m["host"],
                    f"{extra['cpuString']} ({system['cpuArch']}) {extra['cpuFrequencyMHz']} MHz",
                    f"{system['numCores']}c",
                    format_size(system["memSizeMB"] * 1024**2),
                    f"{os['name']} {os['version']}",
                    system["numaEnabled"]
                ])

        enum_result_items(result,
                          func_rs_cluster=func_component,
                          func_all_mongos=func_component,
                          func_shard=func_component,
                          func_config=func_component)
        return {
            "name": self.name,
            "description": self.description,
            "data": data
        }