from libs.check_items.base_item import BaseItem
from libs.shared import *
from libs.utils import *

"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""
class CollInfoItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Collection Information"
        self._description = "Collects & review collection statistics.\n\n"
        self._description += "- Whether average object size is too big.\n"
        self._description += "- Whether collections are big enough for sharding.\n"
        self._description += "- Whether collections are fragmented.\n"

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        
        def enum_collections(name, node, func, **kwargs):
            client = node["client"]
            level = kwargs.get("level")
            host = node["host"] if "host" in node else "cluster"
            dbs = client.admin.command("listDatabases").get("databases", [])
            raw_result = []
            test_result = []
            for db_obj in dbs:
                db_name = db_obj.get("name")
                if db_name in ["admin", "local", "config"]:
                    self._logger.debug(f"Skipping system database: {db_name}")
                    continue
                db = client[db_name]
                collections = db.list_collections()

                for coll_info in collections:
                    coll_name = coll_info.get("name")
                    coll_type = coll_info.get("type", "collection")
                    # TODO: support timeseries collections
                    if coll_type != "collection":
                        self._logger.debug(f"Skipping non-collection type: {coll_name} ({coll_type})")
                        continue
                    if coll_name.startswith("system."):
                        self._logger.debug(f"Skipping system collection: {db_name}.{coll_name}")
                        continue
                    self._logger.debug(f"Gathering stats for collection: `{db_name}.{coll_name}`")

                    args = {"storageStats": {}}
                    if level in ["sh_cluster", "rs_cluster"]:
                        args["latencyStats"] = {"histograms": True}
                    stats = db.get_collection(coll_name).aggregate([{
                        "$collStats": args
                    }]).next()
                    t_result, r_result = func(host, stats, **kwargs)
                    test_result.extend(t_result)
                    raw_result.append(r_result)
            self.append_test_results(test_result)
            return test_result, raw_result

        obj_size_bytes = self._config.get("obj_size_kb", 32) * 1024
        fragmentation_ratio = self._config.get("fragmentation_ratio", 0.5)
        collection_size_gb = self._config.get("collection_size_gb", 2048) * 1024**3

        def func_overview(host, stats, **kwargs):
            test_result = []
            ns = stats["ns"]
            storage_stats = stats.get("storageStats", {})
            del storage_stats["indexDetails"]
            del storage_stats["wiredTiger"]
            # Check for large collection size
            if storage_stats.get("size", 0) > collection_size_gb:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.LOW,
                    "title": "Large Collection Size",
                    "description": f"Collection `{ns}` has size `{storage_stats.get('size', 0) / 1024**3} GB` larger than `{collection_size_gb / 1024**3} GB`. Consider sharding."
                })
            # Check for average object size
            if storage_stats.get("avgObjSize", 0) > obj_size_bytes:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.LOW,
                    "title": "Large Object Size",
                    "description": f"Collection `{ns}` has average object size `{storage_stats.get('avgObjSize', 0) / 1024} KB` larger than `{obj_size_bytes / 1024} KB`. Consider optimizing your data schema."
                })

            # Check index:size ratio
            total_index_size = storage_stats.get("totalIndexSize", 0)
            storage_size = storage_stats.get("storageSize", 0)
            threshold = self._config.get("index_size_ratio", 0.2)
            ratio = total_index_size / storage_size if storage_size > 0 else 0
            if ratio > threshold:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "High Index Storage Ratio",
                    "description": f"Collection `{ns}` has an `index:storage` ratio of `{ratio:.2%}` which is higher than the threshold of `{threshold:.2%}`. Consider optimizing your indexes."
                })
            # TODO: check latency
            return test_result, stats

        def func_node(host, stats, **kwargs):
            ns = stats["ns"]
            test_result = []
            # Check for fragmentation
            storage_stats = stats.get("storageStats", {})
            storage_size = storage_stats["storageSize"]
            coll_reusable = storage_stats["wiredTiger"]["block-manager"]["file bytes available for reuse"]
            coll_frag = round(coll_reusable / storage_size if storage_size else 0, 4)
            if coll_frag > fragmentation_ratio:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "High Collection Fragmentation",
                    "description": f"Collection `{ns}` has a higher fragmentation: `{coll_frag:.2%}` than threshold `{fragmentation_ratio:.2%}`."
                })
            index_frags = []
            for index_name, s in storage_stats["indexDetails"].items():
                reusable = s["block-manager"]["file bytes available for reuse"]
                total_size = s["block-manager"]["file size in bytes"]
                fragmentation = round(reusable / total_size if total_size > 0 else 0, 4)
                index_frags.append({
                    "indexName": index_name,
                    "reusable": reusable,
                    "totalSize": total_size,
                    "fragmentation": fragmentation
                })
                if fragmentation > fragmentation_ratio:
                    test_result.append({
                        "host": host,
                        "severity": SEVERITY.MEDIUM,
                        "title": "High Index Fragmentation",
                        "description": f"Collection `{ns}` index `{index_name}` has a higher index fragmentation: `{fragmentation:.2%}` than threshold `{fragmentation_ratio:.2%}`."
                    })
            return test_result, {
                "ns": ns,
                "collFragmentation": {
                    "reusable": coll_reusable,
                    "totalSize": storage_size,
                    "fragmentation": coll_frag
                },
                "indexFragmentation": index_frags,
                "stats": stats
            }

        nodes = discover_nodes(client, parsed_uri)
        result = enum_all_nodes(nodes,
                                func_sh_cluster=lambda name, node, **kwargs: enum_collections(name, node, func_overview, **kwargs),
                                func_rs_cluster=lambda name, node, **kwargs: enum_collections(name, node, func_overview, **kwargs),
                                func_rs_member=lambda name, node, **kwargs: enum_collections(name, node, func_node, **kwargs),
                                func_shard_member=lambda name, node, **kwargs: enum_collections(name, node, func_node, **kwargs))
        self.captured_sample = result
        
    @property
    def review_result(self):
        result = self.captured_sample
        data = []
        stats_table = {
            "type": "table",
            "caption": f"Storage Stats",
            "columns": [
                {"name": "Namespace", "type": "string"},
                {"name": "Size", "type": "string"},
                {"name": "Storage Size", "type": "string"},
                {"name": "Avg Object Size", "type": "string"},
                {"name": "Total Index Size", "type": "string"},
                {"name": "Index / Storage", "type": "decimal"},
            ],
            "rows": []
        }
        data.append(stats_table)
        def func_overview(set_name, node, **kwargs):
            raw_result = node["rawResult"]
            if raw_result is None:
                stats_table["rows"].append(["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"])
                return
            for stats in raw_result:
                ns = stats["ns"]
                storage_stats = stats.get("storageStats", {})
                size = storage_stats.get("size", 0)
                storage_size = storage_stats.get("storageSize", 0)
                avg_obj_size = storage_stats.get("avgObjSize", 0)
                total_index_size = storage_stats.get("totalIndexSize", 0)
                index_data_ratio = round(total_index_size / storage_size, 4) if size > 0 else 0
                stats_table["rows"].append([escape_markdown(ns),
                                      format_size(size),
                                      format_size(storage_size),
                                      format_size(avg_obj_size),
                                      format_size(total_index_size),
                                      f"{index_data_ratio:.2%}"])
        frag_table = {
            "type": "table",
            "caption": f"Fragmentation",
            "columns": [
                {"name": "Host", "type": "string"},
                {"name": "Namespace", "type": "string"},
                {"name": "Collection Fragmentation", "type": "string"},
                {"name": "Index Fragmentation", "type": "decimal", "align": "left"},
            ],
            "rows": []
        }
        data.append(frag_table)
        def func_node(set_name, node, **kwargs):
            raw_result = node["rawResult"]
            host = node["host"]
            if raw_result is None:
                frag_table["rows"].append([host, "n/a", "n/a", "n/a"])
                return
            for stats in raw_result:
                ns = stats["ns"]
                coll_frag = stats.get("collFragmentation", {}).get("fragmentation", 0)
                index_frags = stats.get("indexFragmentation", [])
                total_reusable_size = 0
                total_index_size = 0
                index_details = []
                for index in index_frags:
                    total_reusable_size += index.get("reusable", 0)
                    total_index_size += index.get("totalSize", 0)
                    index_name = escape_markdown(index.get("indexName", ""))
                    fragmentation = index.get("fragmentation", 0)
                    index_details.append(f"{index_name}: {fragmentation:.2%}")
                index_frag = round(total_reusable_size / total_index_size, 4) if total_index_size > 0 else 0
                row = [host, escape_markdown(ns), f"{coll_frag:.2%}",
                       f"{index_frag:.2%}<br/><pre>{'<br/>'.join(index_details)}</pre>"]
                frag_table["rows"].append(row)
        enum_result_items(result, func_sh_cluster=func_overview, func_rs_cluster=func_overview, func_rs_member=func_node, func_shard_member=func_node)
        return {
            "title": self.name,
            "description": self.description,
            "data": data
        }