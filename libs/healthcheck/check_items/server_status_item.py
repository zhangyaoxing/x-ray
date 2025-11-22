from time import sleep
from libs.healthcheck.check_items.base_item import BaseItem
from libs.healthcheck.shared import SEVERITY, MAX_MONGOS_PING_LATENCY, discover_nodes, enum_all_nodes, enum_result_items
from libs.utils import format_size, escape_markdown, green, yellow

SERVER_STATUS_INTERVAL = 5


class ServerStatusItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Server Status Information"
        self._description = "Collects and reviews server status metrics.\n\n"
        self._description += "- Whether used/total connection ratio is too high.\n"
        self._description += "- Whether query targeting is poor.\n"
        self._description += "- Whether the cache read into rate is too high.\n"

    def _check_connections(self, host, server_status):
        """
        Check the connections metrics.
        """
        test_result = []
        connections = server_status.get("connections", {})
        used_connection_ratio = self._config.get("used_connection_ratio", 0.8)
        available = connections.get("available", 0)
        current = connections.get("current", 0)
        total = available + current
        if current / total > used_connection_ratio:
            test_result.append(
                {
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "High Connection Usage",
                    "description": f"Current connections (`{current}`) exceed `{used_connection_ratio * 100:.2f}%` of total connections (`{total}`).",
                }
            )

        return test_result, connections

    def _check_query_targeting(self, host, server_status):
        """
        Check query targeting metrics.
        """
        test_result = []
        query_executor = server_status["metrics"].get("queryExecutor", {})
        document = server_status["metrics"].get("document", {})
        scanned_returned = (query_executor["scanned"] / document["returned"]) if document["returned"] > 0 else 0
        scanned_obj_returned = (
            (query_executor["scannedObjects"] / document["returned"]) if document["returned"] > 0 else 0
        )
        query_targeting = self._config.get("query_targeting", {})
        query_targeting_obj = self._config.get("query_targeting_obj", {})
        if scanned_returned > query_targeting:
            test_result.append(
                {
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "Poor Query Targeting",
                    "description": f"Scanned/Returned ratio `{scanned_returned:.2f}` exceeds the threshold `{query_targeting}`.",
                }
            )
        if scanned_obj_returned > query_targeting_obj:
            test_result.append(
                {
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "Poor Query Targeting",
                    "description": f"Scanned Objects/Returned ratio `{scanned_obj_returned:.2f}` exceeds the threshold `{query_targeting_obj}`.",
                }
            )

        return test_result, {"scanned/returned": scanned_returned, "scanned_obj/returned": scanned_obj_returned}

    def _check_cache(self, host, ss1, ss2):
        pass

    def test(self, *args, **kwargs):
        """
        Run the server status test.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        def func_first_req(set_name, node, server_status):
            # First request do nothing but return the server status as is.
            # The test will be in the 2nd request.
            return [], {"server_status": server_status}

        def func_2nd_req(set_name, node, server_status):
            host = node["host"]
            test_result1, raw_result1 = self._check_connections(host, server_status)
            test_result2, raw_result2 = (
                self._check_query_targeting(host, server_status) if set_name != "mongos" else ([], None)
            )
            test_result = test_result1 + test_result2
            self.append_test_results(test_result)
            raw_result = {"connections": raw_result1, "query_targeting": raw_result2, "server_status": server_status}

            return test_result, raw_result

        def enumerator(set_name, node, **kwargs):
            host = node["host"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(
                        f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            client = node["client"]
            server_status = client.admin.command("serverStatus")
            func_req = kwargs.get("func_req")
            test_result, raw_result = func_req(set_name, node, server_status)
            return test_result, raw_result

        nodes = discover_nodes(client, parsed_uri)

        def func_all_first(set_name, node, **kwargs):
            return enumerator(set_name, node, func_req=func_first_req, **kwargs)

        result1 = enum_all_nodes(
            nodes,
            func_mongos_member=func_all_first,
            func_rs_member=func_all_first,
            func_shard_member=func_all_first,
            func_config_member=func_all_first,
        )
        # Sleep for 5s to capture next status.
        self._logger.info("Sleep %s to capture next server status.", green(f"{SERVER_STATUS_INTERVAL} seconds"))
        sleep(SERVER_STATUS_INTERVAL)

        def func_all_2nd(set_name, node, **kwargs):
            return enumerator(set_name, node, func_req=func_2nd_req, **kwargs)

        result2 = enum_all_nodes(
            nodes,
            func_mongos_member=func_all_2nd,
            func_rs_member=func_all_2nd,
            func_shard_member=func_all_2nd,
            func_config_member=func_all_2nd,
        )

        # These metrics needs to compare 2 `serverStatus` results
        cache = {}
        read_into_threshold = self._config.get("cache_read_into_mb", 100)

        def func_data_member(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if not raw_result:
                cache[host] = {
                    "setName": set_name,
                    "host": host,
                    "cacheSize": "n/a",
                    "inCacheSize": "n/a",
                    "readInto": "n/a",
                    "writtenFrom": "n/a",
                }
                return

            wt = raw_result["server_status"]["wiredTiger"]
            if host not in cache:
                # Enumerating result1
                cache[host] = {
                    "readInto": wt["cache"]["bytes read into cache"],
                    "writtenFrom": wt["cache"]["bytes written from cache"],
                    "forUpdates": wt["cache"]["bytes allocated for updates"],
                    "dirty": wt["cache"]["bytes dirty in the cache cumulative"],
                    "uptimeMillis": raw_result["server_status"]["uptimeMillis"],
                }
            else:
                # Enumerating result2
                read_into = wt["cache"]["bytes read into cache"]
                written_from = wt["cache"]["bytes written from cache"]
                for_updates = wt["cache"]["bytes allocated for updates"]
                dirty = wt["cache"]["bytes dirty in the cache cumulative"]
                uptime = raw_result["server_status"]["uptimeMillis"]
                interval = (uptime - cache[host]["uptimeMillis"]) / 1000
                cache[host] = {
                    "cacheSize": wt["cache"]["maximum bytes configured"],
                    "inCacheSize": wt["cache"]["bytes currently in the cache"],
                    "readInto": (read_into - cache[host]["readInto"]) / interval,
                    "writtenFrom": (written_from - cache[host]["writtenFrom"]) / interval,
                    "forUpdates": for_updates - cache[host]["forUpdates"],
                    "dirty": dirty - cache[host]["dirty"],
                    "uptimeMillis": (uptime - cache[host]["uptimeMillis"]),
                }
                test_result = []
                if cache[host]["readInto"] >= read_into_threshold * 1024 * 1024:
                    test_result.append(
                        {
                            "host": host,
                            "severity": SEVERITY.MEDIUM,
                            "title": "High Swapping",
                            "description": f"Read into cache rate `{format_size(cache[host]['readInto'])}/s` exceeds the threshold `{format_size(read_into_threshold * 1024 * 1024)}/s`. This usually indicates insufficient cache size or suboptimal indexes.",
                        }
                    )
                self.append_test_results(test_result)
                # Attach the test result and raw result to the original result.
                node["testResult"].extend(test_result)
                node["rawResult"]["cache"] = cache[host]

        enum_result_items(
            result1,
            func_rs_member=func_data_member,
            func_shard_member=func_data_member,
            func_config_member=func_data_member,
        )
        enum_result_items(
            result2,
            func_rs_member=func_data_member,
            func_shard_member=func_data_member,
            func_config_member=func_data_member,
        )

        op_counters = {}

        def func_all_member(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if not raw_result:
                op_counters[host] = {
                    "set_name": set_name,
                    "host": host,
                    "insert": "n/a",
                    "query": "n/a",
                    "update": "n/a",
                    "delete": "n/a",
                    "command": "n/a",
                    "getmore": "n/a",
                }
                return
            ops = raw_result["server_status"]["opcounters"]
            if host not in op_counters:
                op_counters[host] = {
                    "set_name": set_name,
                    "host": host,
                    "insert": ops.get("insert", 0),
                    "query": ops.get("query", 0),
                    "update": ops.get("update", 0),
                    "delete": ops.get("delete", 0),
                    "command": ops.get("command", 0),
                    "getmore": ops.get("getmore", 0),
                }
            else:
                inserts = ops["insert"]
                reads = ops["query"]
                updates = ops["update"]
                deletes = ops["delete"]
                commands = ops["command"]
                getmores = ops["getmore"]
                op_counters[host] = {
                    "set_name": set_name,
                    "host": host,
                    "insert": inserts - op_counters[host]["insert"],
                    "query": reads - op_counters[host]["query"],
                    "update": updates - op_counters[host]["update"],
                    "delete": deletes - op_counters[host]["delete"],
                    "command": commands - op_counters[host]["command"],
                    "getmore": getmores - op_counters[host]["getmore"],
                }
                node["rawResult"]["op_counters"] = op_counters[host]

        enum_result_items(
            result1,
            func_mongos_member=func_all_member,
            func_rs_member=func_all_member,
            func_shard_member=func_all_member,
            func_config_member=func_all_member,
        )
        enum_result_items(
            result2,
            func_mongos_member=func_all_member,
            func_rs_member=func_all_member,
            func_shard_member=func_all_member,
            func_config_member=func_all_member,
        )
        self.captured_sample = [result1, result2]

    @property
    def review_result(self):
        result = self.captured_sample
        _, result2 = result
        data = []
        conn_table = {
            "type": "table",
            "caption": "Connections",
            "notes": "- `Rejected` is only available for MongoDB 6.3 and later.\n"
            + "- `Threaded` is only available for MongoDB 5.0 and later.\n",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Current", "type": "decimal"},
                {"name": "Available", "type": "decimal"},
                {"name": "Active", "type": "decimal"},
                {"name": "Created", "type": "decimal"},
                {"name": "Rejected", "type": "decimal"},
                {"name": "Threaded", "type": "decimal"},
            ],
            "rows": [],
        }
        current = []
        active = []
        data_conn = {}
        opcounters_table = {
            "type": "table",
            "caption": "Operation Counters",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Inserts", "type": "decimal"},
                {"name": "Queries", "type": "decimal"},
                {"name": "Updates", "type": "decimal"},
                {"name": "Deletes", "type": "decimal"},
                {"name": "Commands", "type": "decimal"},
                {"name": "Getmores", "type": "decimal"},
            ],
            "rows": [],
        }
        inserts = []
        queries = []
        updates = []
        deletes = []
        commands = []
        getmores = []
        data_ops = {}
        data.append(conn_table)
        data.append({"type": "chart", "data": data_conn})
        data.append(opcounters_table)
        data.append({"type": "chart", "data": data_ops})

        def func_all_members(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            if not raw_result:
                conn_table["rows"].append(
                    [escape_markdown(set_name), node["host"], "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]
                )
                opcounters_table["rows"].append(
                    [escape_markdown(set_name), node["host"], "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]
                )
                data_conn[f"{set_name}/{node['host']}"] = {
                    "current": 0,
                    "available": 0,
                    "active": 0,
                    "totalCreated": 0,
                    "rejected": 0,
                    "threaded": 0,
                }
                data_ops[f"{set_name}/{node['host']}"] = {
                    "insert": 0,
                    "query": 0,
                    "update": 0,
                    "delete": 0,
                    "command": 0,
                    "getmore": 0,
                }
                return
            host = node["host"]
            conns = raw_result.get("connections", {})
            conn_table["rows"].append(
                [
                    escape_markdown(set_name),
                    host,
                    conns.get("current", 0),
                    conns.get("available", 0),
                    conns.get("active", 0),
                    conns.get("totalCreated", 0),
                    conns.get("rejected", "n/a"),
                    conns.get("threaded", "n/a"),
                ]
            )
            data_conn[f"{set_name}/{host}"] = {
                "current": conns.get("current", 0),
                "available": conns.get("available", 0),
                "active": conns.get("active", 0),
                "totalCreated": conns.get("totalCreated", 0),
                "rejected": conns.get("rejected", 0),
                "threaded": conns.get("threaded", 0),
            }
            active.append(conns.get("active", 0))
            current.append(conns.get("current", 0) - conns.get("active", 0))
            opcounters = raw_result.get("op_counters", {})
            opcounters_table["rows"].append(
                [
                    escape_markdown(set_name),
                    host,
                    opcounters.get("insert", 0),
                    opcounters.get("query", 0),
                    opcounters.get("update", 0),
                    opcounters.get("delete", 0),
                    opcounters.get("command", 0),
                    opcounters.get("getmore", 0),
                ]
            )
            data_ops[f"{set_name}/{host}"] = {
                "insert": opcounters.get("insert", 0),
                "query": opcounters.get("query", 0),
                "update": opcounters.get("update", 0),
                "delete": opcounters.get("delete", 0),
                "command": opcounters.get("command", 0),
                "getmore": opcounters.get("getmore", 0),
            }
            inserts.append(opcounters.get("insert", 0))
            queries.append(opcounters.get("query", 0))
            updates.append(opcounters.get("update", 0))
            deletes.append(opcounters.get("delete", 0))
            commands.append(opcounters.get("command", 0))
            getmores.append(opcounters.get("getmore", 0))

        enum_result_items(
            result2,
            func_mongos_member=func_all_members,
            func_rs_member=func_all_members,
            func_shard_member=func_all_members,
            func_config_member=func_all_members,
        )
        qt_table = {
            "type": "table",
            "caption": "Query Targeting",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Scanned / Returned", "type": "decimal"},
                {"name": "Scanned Objects / Returned", "type": "decimal"},
            ],
            "rows": [],
        }
        cache_table = {
            "type": "table",
            "caption": "WiredTiger Cache",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Cache Size", "type": "decimal"},
                {"name": "In-Cache Size", "type": "decimal"},
                {"name": "Read Into", "type": "decimal"},
                {"name": "Written From", "type": "decimal"},
            ],
            "rows": [],
        }
        cache_sizes = []
        in_cache_sizes = []
        read_into_sizes = []
        written_from_sizes = []
        data_cache = {}
        data.append(cache_table)
        data.append({"type": "chart", "data": data_cache})
        data.append(qt_table)

        def func_data_member(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if not raw_result:
                cache_table["rows"].append([escape_markdown(set_name), host, "n/a", "n/a", "n/a", "n/a"])
                qt_table["rows"].append([escape_markdown(set_name), node["host"], "n/a", "n/a"])
                data_cache[f"{set_name}/{host}"] = {
                    "cacheSize": 0,
                    "inCacheSize": 0,
                    "readInto": 0,
                    "forUpdates": 0,
                    "dirty": 0,
                    "writtenFrom": 0,
                }
                return
            cache = raw_result.get("cache", {})
            cache_table["rows"].append(
                [
                    escape_markdown(set_name),
                    escape_markdown(host),
                    format_size(cache.get("cacheSize", 0)),
                    format_size(cache.get("inCacheSize", 0)),
                    f"{format_size(cache.get('readInto', 0))}/s",
                    f"{format_size(cache.get('writtenFrom', 0))}/s",
                ]
            )
            data_cache[f"{set_name}/{host}"] = {
                "cacheSize": cache.get("cacheSize", 0),
                "inCacheSize": cache.get("inCacheSize", 0),
                "readInto": cache.get("readInto", 0),
                "forUpdates": cache.get("forUpdates", 0),
                "dirty": cache.get("dirty", 0),
                "writtenFrom": cache.get("writtenFrom", 0),
            }
            cache_sizes.append(cache.get("cacheSize", 0))
            in_cache_sizes.append(cache.get("inCacheSize", 0))
            read_into_sizes.append(cache.get("readInto", 0))
            written_from_sizes.append(cache.get("writtenFrom", 0))
            query_targeting = raw_result.get("query_targeting", {})
            qt_table["rows"].append(
                [
                    escape_markdown(set_name),
                    host,
                    f"{query_targeting.get('scanned/returned', 0):.2f}",
                    f"{query_targeting.get('scanned_objects/returned', 0):.2f}",
                ]
            )

        enum_result_items(
            result2,
            func_rs_member=func_data_member,
            func_shard_member=func_data_member,
            func_config_member=func_data_member,
        )

        return {"name": self.name, "description": self.description, "data": data}
