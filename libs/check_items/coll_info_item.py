from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from libs.check_items.base_item import BaseItem, SEVERITY
from libs.utils import *

"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""
class CollInfoItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Collection Information"
        self._description = "Collects & review collection statistics."

    def _fragmentation_check(self, stats, threshold=0.5):
        """
        Check for fragmentation in the collection.
        """
        def get_details(id, s):
            detail = {
                "id": id,
                "size": s.get("size", 0),
                "storage_size": s.get("storageSize", 0),
                "coll_reusable": s["wiredTiger"]["block-manager"]["file bytes available for reuse"],
                "total_index_size": s.get("totalIndexSize", 0),
                "index_reusable": 0
            }
            if "indexDetails" in s:
                detail["index_reusable"] = sum(
                    index["block-manager"]["file bytes available for reuse"] for index in s["indexDetails"].values()
                )
                return detail
            else:
                self._logger.warning(yellow(f"No index details found for collection {id}. Skipping index space calculation."))
                return None

        results = []
        if "sharded" in stats and stats["sharded"]:
            for name, shard in stats.get("shards", []).items():
                results.append(get_details(f"{name}-{stats['ns']}", shard))
        else:
            results.append(get_details(stats["ns"], stats))

        for detail in results:
            storage_size = detail.get("storage_size", 0)
            total_index_size = detail.get("total_index_size", 0)
            coll_reusable = detail.get("coll_reusable", 0)
            index_reusable = detail.get("index_reusable", 0)
            coll_frag = coll_reusable / storage_size if storage_size else 0
            index_frag = index_reusable / total_index_size if total_index_size else 0
            if coll_frag > threshold:
                self.append_item_result(
                    SEVERITY.MEDIUM,
                    "High Collection Fragmentation",
                    f"Collection `{detail['id']}` has a higher fragmentation: `{coll_frag:.2%}` than threshold `{threshold:.2%}`."
                )
            if index_frag > threshold:
                self.append_item_result(
                    SEVERITY.MEDIUM,
                    "High Index Fragmentation",
                    f"Collection `{detail['id']}` has a higher index fragmentation: `{index_frag:.2%}` than threshold `{threshold:.2%}`."
                )
        
    def _imbalance_check(self, ns, stats, shards, threshold=0.3):
        """
        Check for sharding imbalance in the collection.
        """
        shard_names = [s["_id"] for s in shards]
        if "sharded" in stats and stats["sharded"]:
            sizes = [{"shard": n, "size": s["size"]} for n, s in stats["shards"].items()]
            sorted_sizes = sorted(sizes, key=lambda x: x["size"], reverse=True)
            high = sorted_sizes[0]
            if len(sorted_sizes) < len(shards):
                # Find name that exists in shard_names but not in sorted_sizes
                missing_shards = set(shard_names) - {s["shard"] for s in sorted_sizes}
                low = {"shard": list(missing_shards)[0], "size": 0}
                imbalance_percent = 1.0  # If not all shards have data, consider it imbalanced
            else:
                low = sorted_sizes[-1]
                imbalance_percent = (high["size"] - low["size"]) / low["size"]
            if imbalance_percent > threshold:
                self.append_item_result(
                    SEVERITY.MEDIUM,
                    "Sharding Imbalance",
                    f"Sharding imbalance detected in `{ns}`: `{high['shard']}` has `{imbalance_percent:.2%}` more data than `{low['shard']}`."
                )

    def _check_obj_size(self, ns, stats, obj_size_bytes):
        """ Check for average object size in the collection.
        """
        if stats.get("avgObjSize", 0) > obj_size_bytes:
            self.append_item_result(
                SEVERITY.LOW,
                "Large Object Size",
                f"Collection `{ns}` has average object size `{stats.get('avgObjSize', 0) / 1024} KB` larger than `{obj_size_bytes / 1024} KB`."
            )

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering collection statistics...")
        client = kwargs.get("client")
        dbs = client.admin.command("listDatabases").get("databases", [])
        all_stats = []
        for db_obj in dbs:
            db_name = db_obj.get("name")
            if db_name in ["admin", "local", "config"]:
                self._logger.info(f"Skipping system database: {db_name}")
                continue
            db = client[db_name]
            collections = db.list_collections()
            obj_size_bytes = self._config.get("obj_size_kb", 32) * 1024
            sharding_imbalance_percentage = self._config.get("sharding_imbalance_percentage", 0.3)
            fragmentation_ratio = self._config.get("fragmentation_ratio", 0.5)
            shards = list(client["config"].get_collection("shards").find())
  
            for coll_info in collections:
                coll_name = coll_info.get("name")
                coll_type = coll_info.get("type", "collection")
                if coll_type != "collection":
                    self._logger.debug(f"Skipping non-collection type: {coll_name} ({coll_type})")
                    continue
                if coll_name.startswith("system."):
                    self._logger.debug(f"Skipping system collection: {db_name}.{coll_name}")
                    continue
                self._logger.info(f"Gathering stats for collection: `{db_name}.{coll_name}`")
                ns = f"{db_name}.{coll_name}"
                try:
                    stats = db.command("collStats", coll_name, indexDetails=True)
                    all_stats.append({ns: stats})
                    # Check for average object size
                    self._check_obj_size(ns, stats, obj_size_bytes)

                    # Check for sharding imbalance
                    self._imbalance_check(ns, stats, shards, sharding_imbalance_percentage)

                    # Check for fragmentation
                    self._fragmentation_check(stats, fragmentation_ratio)
                    
                except Exception as e:
                    self._logger.error(red(f"Failed to gather stats for collection '{ns}': {str(e)}"))

        self.sample_result = all_stats