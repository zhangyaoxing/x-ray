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
        self._description += "- Whether collections and indexes are fragmented.\n"
        self._description += "- Whether operation latency exceeds thresholds.\n"

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        
        def enum_collections(name, node, func, **kwargs):
            client = node["client"]
            latency = node.get("pingLatencySec", 0)
            level = kwargs.get("level")
            host = node["host"] if "host" in node else "cluster"
            if latency > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(yellow(f"Skip {host} because it has been irresponsive for {latency / 60:.2f} minutes."))
                return None, None
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
            # Check operation latency
            latency_stats = stats.get("latencyStats", {})
            reads, writes, commands, transactions = latency_stats["reads"], latency_stats["writes"], latency_stats["commands"], latency_stats["transactions"]
            r_latency, w_latency, c_latency, t_latency = reads["latency"], writes["latency"], commands["latency"], transactions["latency"]
            r_ops, w_ops, c_ops, t_ops = reads["ops"], writes["ops"], commands["ops"], transactions["ops"]
            avg_r_latency = r_latency / r_ops if r_ops > 0 else 0
            avg_w_latency = w_latency / w_ops if w_ops > 0 else 0
            avg_c_latency = c_latency / c_ops if c_ops > 0 else 0
            avg_t_latency = t_latency / t_ops if t_ops > 0 else 0
            op_latency_ms = self._config.get("op_latency_ms", 100)
            if avg_r_latency > op_latency_ms:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "High Read Latency",
                    "description": f"Collection `{ns}` has a higher average read latency `{avg_r_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`."
                })
            if avg_w_latency > op_latency_ms:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "High Write Latency",
                    "description": f"Collection `{ns}` has a higher average write latency `{avg_w_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`."
                })
            if avg_c_latency > op_latency_ms:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "High Command Latency",
                    "description": f"Collection `{ns}` has a higher average command latency `{avg_c_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`."
                })
            if avg_t_latency > op_latency_ms:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "High Transaction Latency",
                    "description": f"Collection `{ns}` has a higher average transaction latency `{avg_t_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`."
                })
            return test_result, {
                "ns": ns,
                "collFragmentation": {
                    "reusable": coll_reusable,
                    "totalSize": storage_size,
                    "fragmentation": coll_frag
                },
                "indexFragmentation": index_frags,
                "latencyStats": {
                    "reads_latency": avg_r_latency,
                    "writes_latency": avg_w_latency,
                    "commands_latency": avg_c_latency,
                    "transactions_latency": avg_t_latency
                },
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
        data_sizes = []
        data_size_pie = {
            "type": "pie",
            "data": {
                "labels": [],
                "datasets": [{
                    "label": "Data Sizes",
                    "data": data_sizes
                }]
            },
            "options": {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Data Size"
                    }
                }
            }
        }
        index_sizes = []
        index_size_pie = {
            "type": "pie",
            "data": {
                "labels": [],
                "datasets": [{
                    "label": "Index Sizes",
                    "data": index_sizes
                }]
            },
            "options": {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Index Size"
                    }
                }
            }
        }
        data.append(data_size_pie)
        data.append(index_size_pie)
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
                data_size_pie["data"]["labels"].append(f"{ns}")
                data_sizes.append(size)
                index_size_pie["data"]["labels"].append(f"{ns}")
                index_sizes.append(total_index_size)
        frag_table = {
            "type": "table",
            "caption": f"Storage Fragmentation",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Namespace", "type": "string"},
                {"name": "Collection Fragmentation", "type": "string"},
                {"name": "Index Fragmentation", "type": "decimal", "align": "left"},
            ],
            "rows": []
        }
        labels = set()
        hosts = set()
        frag_data = []
        coll_frag_bar = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "scales": {
                    "x": {
                        "stacked": False
                    },
                    "y": {
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "Storage Fragmentation Ratio"
                        }
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Storage Fragmentation"
                    }
                }
            }
        }
        index_frag_bar = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "scales": {
                    "x": {
                        "stacked": False
                    },
                    "y": {
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "Index Fragmentation Ratio"
                        }
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Index Fragmentation"
                    }
                }
            }
        }
        latency_table = {
            "type": "table",
            "caption": f"Operation Latency",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Namespace", "type": "string"},
                {"name": "Read Latency", "type": "string"},
                {"name": "Write Latency", "type": "decimal"},
                {"name": "Command Latency", "type": "decimal"},
                {"name": "Transaction Latency", "type": "decimal"},
            ],
            "rows": []
        }
        data.append(frag_table)
        data.append(coll_frag_bar)
        data.append(index_frag_bar)
        data.append(latency_table)
        def func_node(set_name, node, **kwargs):
            raw_result = node["rawResult"]
            host = node["host"]
            if raw_result is None:
                frag_table["rows"].append([host, "n/a", "n/a", "n/a"])
                return
            for stats in raw_result:
                ns = stats["ns"]
                labels.add(ns)
                # Fragmentation visualization
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
                frag_table["rows"].append([escape_markdown(set_name), host, escape_markdown(ns), f"{coll_frag:.2%}",
                       f"{index_frag:.2%}<br/><pre>{'<br/>'.join(index_details)}</pre>"])
                label = f"{set_name}/{host}"
                hosts.add(label)
                frag_data.append({
                    "label": label,
                    "ns": ns,
                    "collFrag": coll_frag,
                    "indexFrag": index_frag
                })
                # Latency visualization
                avg_reads_latency = stats.get("latencyStats", {}).get("reads_latency", 0)
                avg_writes_latency = stats.get("latencyStats", {}).get("writes_latency", 0)
                avg_commands_latency = stats.get("latencyStats", {}).get("commands_latency", 0)
                avg_transactions_latency = stats.get("latencyStats", {}).get("transactions_latency", 0)
                latency_table["rows"].append([escape_markdown(set_name), host, escape_markdown(ns), f"{avg_reads_latency:.2f}ms",
                                                f"{avg_writes_latency:.2f}ms", f"{avg_commands_latency:.2f}ms",
                                                f"{avg_transactions_latency:.2f}ms"])
        enum_result_items(result, func_sh_cluster=func_overview, func_rs_cluster=func_overview, func_rs_member=func_node, func_shard_member=func_node)
        labels = list(labels)
        hosts = list(hosts)
        labels.sort()
        hosts.sort()
        coll_frag_bar["data"]["labels"] = labels
        index_frag_bar["data"]["labels"] = labels
        for label in hosts:
            ns_data = []
            idx_data = []
            for ns in labels:
                search = [item for item in frag_data if item["label"] == label and item["ns"] == ns]
                v = search[0]["collFrag"] if len(search) > 0 else 0
                ns_data.append(v)
                v = search[0]["indexFrag"] if len(search) > 0 else 0
                idx_data.append(v)
            coll_frag_bar["data"]["datasets"].append({
                "label": label,
                "data": ns_data,
                "stack": label
            })
            index_frag_bar["data"]["datasets"].append({
                "label": label,
                "data": idx_data
            })

        return {
            "title": self.name,
            "description": self.description,
            "data": data
        }