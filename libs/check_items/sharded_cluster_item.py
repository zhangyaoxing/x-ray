from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from libs.check_items.base_item import BaseItem
from libs.shared import *
from libs.utils import *

class ShardedClusterItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Sharded Cluster Information"
        self._description = "Collects and reviews sharded cluster configuration and status."

    def _check_rs(self, info):
        """
        Check if the replica set config and status.
        """
        sample_result = {}
        for member in info["members"]:
            uri = member["uri"]
            try:
                client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                replset_status, replset_config = gather_replset_info(client)

                # Check replica set status and config
                result = check_replset_status(replset_status, self._config)
                for item in result:
                    self.append_item_result(item["host"], item["severity"], item["title"], item["description"])
                result = check_replset_config(replset_config, self._config)
                for item in result:
                    self.append_item_result(item["host"], item["severity"], item["title"], item["description"])
                # Check oplog window
                raw_oplog_info, result = check_oplog_window(info, self._config)
                for item in result:
                    self.append_item_result(item["host"], item["severity"], item["title"], item["description"])

                sample_result[member["host"]] = {
                    "replset_status": replset_status,
                    "replset_config": replset_config,
                    "oplog": raw_oplog_info
                }
            except Exception as e:
                self._logger.error(red(f"Failed to connect to shard `{member['host']}`: {str(e)}"))
                sample_result[member["host"]] = None
        return sample_result

    def _check_mongos(self, nodes):
        """
        Check if the mongos is available and connected.
        """
        all_mongos = nodes["map"]["mongos"]["members"]
        active_mongos = []
        for mongos in all_mongos:
            if mongos.get("pingLatencySec", 0) > MAX_MONGOS_PING_LATENCY:
                self.append_item_result(
                    mongos["host"],
                    SEVERITY.LOW,
                    "Irresponsive Mongos",
                    f"Mongos `{mongos['host']}` is not responsive. Last ping was at `{round(mongos['pingLatencySec'])}` seconds ago. This is expected if the mongos has been removed from the cluster."
                )
            else:
                active_mongos.append(mongos["host"])

        if len(active_mongos) == 0:
            self.append_item_result(
                "cluster",
                SEVERITY.HIGH,
                "No Active Mongos",
                "No active mongos found in the cluster."
            )
        if len(active_mongos) == 1:
            self.append_item_result(
                active_mongos[0],
                SEVERITY.HIGH,
                "Single Mongos",
                f"Only one mongos `{active_mongos[0]}` is available in the cluster. No failover is possible."
            )
        return {
            mongos["host"]: {
                "pingLatencySec": mongos["pingLatencySec"]
            } for mongos in all_mongos
        }

    def test(self, *args, **kwargs):
        """
        Main test method to gather sharded cluster information.
        """
        self._logger.info(f"Gathering sharded cluster info...")
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        is_master = client.admin.command("isMaster")
        if "setName" in is_master:
            self._logger.warning(yellow("This MongoDB instance is not part of a sharded cluster. Skipping..."))
            return
        nodes = discover_nodes(client, parsed_uri)
        sample_result = {}
        for component, info in nodes["map"].items():
            if component == "mongos":
                result = self._check_mongos(nodes)
            else:
                result = self._check_rs(info)

            sample_result[component] = result

        self.captured_sample = sample_result