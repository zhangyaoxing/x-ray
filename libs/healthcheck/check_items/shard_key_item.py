from libs.healthcheck.check_items.base_item import BaseItem
from libs.healthcheck.shared import SEVERITY, discover_nodes, enum_all_nodes, enum_result_items, format_json_md
from libs.utils import format_size, escape_markdown

class ShardKeyItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Shard Key Information"
        self._description = "Collects and reviews shard key configuration for collections in a sharded cluster.\n\n"
        self._description += "- Whether the shard key is set to `{_id: 1}` or `{_id: -1}`.\n"
        self._description += "- Whether collections are imbalanced."

    def test(self, *args, **kwargs):
        """
        Main test method to gather shard key information.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)
        if nodes["type"] == "RS":
            self._logger.info("Cluster is not a sharded cluster. Skip...")
            return
        
        def func_sh_cluster(name, node, **kwargs):
            client = node["client"]
            imbalance_percentage = self._config["sharding_imbalance_percentage"]
            collections = list(client.config.collections.find({"_id": {"$ne": 'config.system.sessions'}}))
            shards = [doc["_id"] for doc in client.config.shards.find()]
            test_result = []
            raw_result = {
                "shardedCollections": collections,
                "stats": {}
            }
            for c in collections:
                # Check if the collection is using `{_id: 1}` as shard key
                ns = c["_id"]
                key = c["key"]
                v = key.get("_id", None)
                if (v == 1 or v == -1) and len(key.keys()) == 1:
                    test_result.append({
                        "host": "cluster",
                        "severity": SEVERITY.INFO,
                        "title": "Improper Shard Key",
                        "description": f"Collection `{ns}` has the shard key set to `{{_id: {v}}}`. Make sure the value of `_id` is not monotonically increasing or decreasing."
                    })
                db_name, coll_name = ns.split(".")
                stats = client[db_name].command("collStats", coll_name)
                shard_stats = {s_name: {
                    "size": s["size"],
                    "count": s["count"],
                    "avgObjSize": s.get("avgObjSize", 0),
                    "storageSize": s["storageSize"],
                    "nindexes": s["nindexes"],
                    "totalIndexSize": s["totalIndexSize"],
                    "totalSize": s["totalSize"]
                } for s_name, s in stats["shards"].items()}
                raw_result["stats"][ns] = shard_stats
                # Check if collection is imbalanced.
                sizes = [shard_stats.get(s_name, {}).get("size", 0) for s_name in shards]
                max_size = max(sizes)
                min_size = min(sizes)
                if max_size > min_size * (1 + imbalance_percentage):
                    test_result.append({
                        "host": "cluster",
                        "severity": SEVERITY.MEDIUM,
                        "title": "Sharding Imbalance",
                        "description": f"Collection `{ns}` is imbalanced across shards. The difference between the largest and smallest shard {(max_size - min_size) / 1024 / 1024:.2f} MB is more than {imbalance_percentage * 100:.2f}%.",
                    })
            self.append_test_results(test_result)
            return test_result, raw_result
        result = enum_all_nodes(nodes, func_sh_cluster=func_sh_cluster)

        self.captured_sample = result

    @property
    def review_result(self):
        result = self.captured_sample
        if result is None:
            return {
                "name": self.name,
                "description": self.description,
                "data": []
            }
        table = {
            "type": "table",
            "caption": f"Shard Keys",
            "columns": [
                {"name": "Namespace", "type": "string"},
                {"name": "Shard Key", "type": "string"},
                {"name": "Data Size", "type": "object", "align": "left"},
                {"name": "Storage Size", "type": "object", "align": "left"},
                {"name": "Index Size", "type": "object", "align": "left"},
                {"name": "Docs Count", "type": "object", "align": "left"}
            ],
            "rows": []
        }
        def func_cluster(name, node, **kwargs):
            raw_result = node["rawResult"]
            if raw_result is None:
                table["rows"].append(["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"])
                return
            collections = raw_result["shardedCollections"]
            all_stats = raw_result["stats"]
            for coll in collections:
                ns = coll["_id"]
                key = coll["key"]
                key_md = escape_markdown(format_json_md(key, indent=None))
                stats = all_stats.get(ns, {})
                data_size = sum(s["size"] for s in stats.values())
                data_size_detail = "<br/>".join([f"{escape_markdown(s_name)}: {format_size(s['size'])}" for s_name, s in stats.items()])
                storage_size = sum(s["storageSize"] for s in stats.values())
                storage_size_detail = "<br/>".join([f"{escape_markdown(s_name)}: {format_size(s['storageSize'])}" for s_name, s in stats.items()])
                index_size = sum(s["totalIndexSize"] for s in stats.values())
                index_size_detail = "<br/>".join([f"{escape_markdown(s_name)}: {format_size(s['totalIndexSize'])}" for s_name, s in stats.items()])
                docs_count = sum(s["count"] for s in stats.values())
                docs_count_detail = "<br/>".join([f"{escape_markdown(s_name)}: {s['count']}" for s_name, s in stats.items()])
                table["rows"].append([escape_markdown(ns), key_md, 
                                    f"{format_size(data_size)}<br/><pre>{data_size_detail}</pre>", 
                                    f"{format_size(storage_size)}<br/><pre>{storage_size_detail}</pre>", 
                                    f"{format_size(index_size)}<br/><pre>{index_size_detail}</pre>", 
                                    f"{docs_count}<br/><pre>{docs_count_detail}</pre>"
                ])
        enum_result_items(result, func_sh_cluster=func_cluster)
        return {
            "name": self.name,
            "description": self.description,
            "data": [table]
        }
