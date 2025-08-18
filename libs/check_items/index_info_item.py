from datetime import datetime, timezone
from libs.check_items.base_item import BaseItem
from libs.shared import SEVERITY, discover_nodes, enum_all_nodes, enum_result_items
from libs.utils import *
from pymongo.uri_parser import parse_uri

"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""
class IndexInfoItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Index Information"
        self._description = "Collects & review index statistics. \n\n"
        self._description += "- Check for the number of indexes in the collection.\n"
        self._description += "- Check for unused indexes in the collection.\n"
        self._description += "- Check for redundant indexes in the collection.\n"

    def _num_indexes_check(self, ns, index_stats, num_indexes, host):
        """ Check for the number of indexes in the collection.
        """
        test_result = []
        if len(index_stats) > num_indexes:
            test_result.append({
                "host": host,
                "severity": SEVERITY.MEDIUM,
                "title": "Too Many Indexes",
                "description": f"Collection `{ns}` has more than `{num_indexes}` indexes, which can cause potential write performance issues."
            })
        return test_result
    
    def _unused_indexes_check(self, ns, index_stats, unused_index_days, host):
        """
        Check for unused indexes in the collection.
        """
        test_result = []
        for index in index_stats:
            if index.get("accesses", {}).get("ops", 0) == 0:
                last_used = index.get("accesses", {}).get("since", None)
                if last_used:
                    if (datetime.now() - last_used).days > unused_index_days:
                        test_result.append({
                            "host": host,
                            "severity": SEVERITY.LOW,
                            "title": "Unused Index",
                            "description": f"Index `{index.get('name')}` from collection `{ns}` has not been used for more than `{unused_index_days}` days."
                        })
        return test_result

    def _redundant_indexes_check(self, ns, indexes, host):
        """
        Check for redundant indexes in the collection.
        """
        test_result = []
        def is_redundant(index1, index2):
            # These options must be identical for indexes to be considered redundant
            OPTIONS = ["unique", "sparse", "partialFilterExpression", "collation", "hidden"]
            for o in OPTIONS:
                if index1.get(o) != index2.get(o):
                    return False
            # Check if the keys are identical or if one is a prefix of the other
            key1 = "_".join([f"{k}_{v}" for k, v in index1["key"].items()])
            key2 = "_".join([f"{k}_{v}" for k, v in index2["key"].items()])

            # If key1 == key2, it's being compared to itself, so skip
            return key1 != key2 and key2.startswith(key1)

        reverse_indexes = []
        for index in indexes:
            reverse_index = {k: v for k, v in index.items() if k != "key"}
            reverse_index["key"] = {k: (v * -1 if isinstance(v, (int, float)) else v) for k, v in index["key"].items()}
            reverse_indexes.append(reverse_index)
        index_targets = indexes + reverse_indexes
        for index in indexes:
            for target in index_targets:
                if is_redundant(index, target):
                    test_result.append({
                        "host": host,
                        "severity": SEVERITY.MEDIUM,
                        "title": "Redundant Index",
                        "description": f"Index `{index.get('name')}` in collection `{ns}` is redundant with index `{target.get('name')}`."
                    })
                    break
        return test_result

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)
        def cluster_check(host, ns, index_stats):
            # Check number of indexes
            max_num_indexes = self._config.get("num_indexes", 10)
            result1 = self._num_indexes_check(ns, index_stats, max_num_indexes, host)
            # Check for redundant indexes
            indexes = [index["spec"] for i, index in enumerate(index_stats)]
            result2 = self._redundant_indexes_check(ns, indexes, host)
            return result1 + result2
        def node_check(host, ns, index_stats):
            unused_index_days = self._config.get("unused_index_days", 7)
            return self._unused_indexes_check(ns, index_stats, unused_index_days, host)
        def enum_namespaces(node, func):
            client = node["client"]
            dbs = client.admin.command("listDatabases").get("databases", [])
            test_result, raw_result = [], []
            host = node.get("host", "cluster")
            for db_obj in dbs:
                db_name = db_obj.get("name")
                if db_name in ["admin", "local", "config"]:
                    self._logger.info(f"Skipping system database: {db_name}")
                    continue
                db = client[db_name]
                collections = db.list_collections()

                for coll_info in collections:
                    coll_name = coll_info.get("name")
                    coll_type = coll_info.get("type", "collection")
                    if coll_type != "collection":
                        self._logger.debug(f"Skipping non-collection type: {coll_name} ({coll_type})")
                        continue
                    if coll_name.startswith("system."):
                        self._logger.debug(f"Skipping system collection: {db_name}.{coll_name}")
                        continue
                    self._logger.info(f"Gathering index stats of collection `{db_name}.{coll_name}` {'on cluster level' if 'type' in node else 'on node level'}...")
                    ns = f"{db_name}.{coll_name}"
                    
                    try:
                        # Check for number of indexes
                        index_stats = list(db[coll_name].aggregate([
                            {"$indexStats": {}}
                        ]))
                        result = func(host, ns, index_stats)
                        test_result.extend(result)
                        raw_result.append({
                            "ns": ns,
                            "captureTime": datetime.now(timezone.utc),
                            "indexStats": index_stats
                        })
                    except Exception as e:
                        self._logger.error(red(f"Failed to gather index info of collection '{ns}': {str(e)}"))
            self.append_test_results(test_result)
            return test_result, raw_result
        result = enum_all_nodes(nodes, 
                                func_rs_cluster=lambda name, node: enum_namespaces(node, cluster_check),
                                func_sh_cluster=lambda name, node: enum_namespaces(node, cluster_check),
                                func_rs_member=lambda name, node: enum_namespaces(node, node_check),
                                func_shard_member=lambda name, node: enum_namespaces(node, node_check))

        self.captured_sample = result
        
    @property
    def review_result(self):
        result = self.captured_sample
        # TODO: display index options? (Unique, sparse, partial...)
        table = {
            "type": "table",
            "caption": f"Index Review",
            "columns": [
                {"name": "Namespace", "type": "string"},
                {"name": "Shard", "type": "string"},
                {"name": "Name", "type": "string"},
                {"name": "Key", "type": "string"},
                {"name": "Access per Hour", "type": "string"}
            ],
            "rows": []
        }
        def review_cluster(set_name, node):
            raw = node.get("rawResult", [])
            for item in raw:
                ns = item["ns"]
                capture_time = item["captureTime"]
                for stats in item["indexStats"]:
                    shard = stats.get("shard", "n/a")
                    access = stats["accesses"]
                    ops = access.get("ops", 0)
                    since = access.get("since", None)
                    access_per_hour = ops / (capture_time - since).total_seconds() / 3600
                    table["rows"].append(
                        [ns, shard, stats["name"], stats["key"], access_per_hour]
                    )

        enum_result_items(result, func_sh_cluster=review_cluster, func_rs_cluster=review_cluster)
        return {
            "name": self.name,
            "description": self.description,
            "data": [table]
        }