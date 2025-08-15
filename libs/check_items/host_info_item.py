
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from libs.check_items.base_item import BaseItem
from libs.shared import discover_nodes, enum_all_nodes, enum_result_items
from libs.utils import red, yellow


class HostInfoItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Host Information"
        self._description = "Collects and reviews host hardware and OS information."

    def test(self, *args, **kwargs):
        """
        Main test method to gather host information.
        """
        self._logger.info(f"Gathering host info...")
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)

        def func_single(name, node):
            client = node["client"]
            if "pingLatencySec" in node and node["pingLatencySec"] > 60:
                self._logger.warning(yellow(f"Skip {node['host']} because its last heartbeat is earlier than 60s ago."))
                return None, None
            host_info = client.admin.command("hostInfo")
            return None, host_info
        raw_result = enum_all_nodes(nodes, func_rs_member=func_single, func_mongos=func_single)

        self.captured_sample = raw_result

    @property
    def review_result(self):
        """
        Review the gathered host information.
        """
        result = self.captured_sample
        data = []

        def func_component(name, node):
            members = node["members"]
            table = {
                "type": "table",
                "caption": f"Hardware & OS Information ({name})",
                "columns": [
                    {"name": "Host", "type": "string"},
                    {"name": "CPU", "type": "string"},
                    {"name": "NUMA", "type": "boolean"},
                    {"name": "Memory (GB)", "type": "string"},
                    {"name": "OS", "type": "string"},
                ],
                "rows": []
            }
            data.append(table)
            for m in members:
                info = m.get("rawResult", None)
                if info is None:
                    table["rows"].append([m["host"], "N/A", "N/A", "N/A", "N/A"])
                    continue
                system = info["system"]
                os = info["os"]
                extra = info["extra"]
                table["rows"].append([
                    m["host"],
                    f"{extra['cpuString']} ({system['cpuArch']}) {extra['cpuFrequencyMHz']} MHz {system['numCores']} cores",
                    system["numaEnabled"],
                    system["memSizeMB"] / 1024,
                    f"{os['name']} {os['version']}"
                ])

        enum_result_items(result, func_rs=func_component, func_all_mongos=func_component)
        return {
            "name": self.name,
            "description": self._description,
            "data": data
        }