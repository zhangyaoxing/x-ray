from libs.healthcheck.check_items.base_item import BaseItem
from libs.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    SEVERITY,
    MEMBER_STATE,
    enum_all_nodes,
    discover_nodes,
    enum_result_items,
)
from libs.utils import yellow, escape_markdown


class ClusterItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Cluster Information"
        self._description = "Collects and reviews cluster configuration and status.\n\n"
        self._description += "- The following items apply to replica set, shards and CSRS:\n"
        self._description += "    - Replication status check.\n"
        self._description += "    - Replication config check.\n"
        self._description += "    - Oplog window check (Both `oplogMinRetentionHours` and oplog size are considered).\n"
        self._description += "- Whether there are irresponsive mongos nodes.\n"
        self._description += "- Whether active mongos nodes are enough.\n"

    def _check_rs(self, set_name, node, **kwargs):
        """
        Run the cluster level checks
        """
        client = node["client"]
        latency = node.get("pingLatencySec", 0)
        if latency > MAX_MONGOS_PING_LATENCY:
            self._logger.warning(
                yellow(f"Skip {node['host']} because it has been irresponsive for {latency / 60:.2f} minutes.")
            )
            return None, None
        test_result = []
        replset_status = client.admin.command("replSetGetStatus")
        replset_config = client.admin.command("replSetGetConfig")
        raw_result = {
            "replsetStatus": replset_status,
            "replsetConfig": replset_config,
        }

        # Check replica set status and config
        result = check_replset_status(replset_status, self._config)
        test_result.extend(result)
        result = check_replset_config(replset_config, self._config)
        test_result.extend(result)

        self.append_test_results(test_result)

        return test_result, raw_result

    def _check_sh(self, set_name, node, **kwargs):
        """
        Check if the sharded cluster is available and connected.
        """
        test_result = []
        all_mongos = node["map"]["mongos"]["members"]
        active_mongos = []
        for mongos in all_mongos:
            if mongos.get("pingLatencySec", 0) > MAX_MONGOS_PING_LATENCY:
                test_result.append(
                    {
                        "host": mongos["host"],
                        "severity": SEVERITY.LOW,
                        "title": "Irresponsive Mongos",
                        "description": f"Mongos `{mongos['host']}` is not responsive. Last ping was at `{round(mongos['pingLatencySec'])}` seconds ago. This is expected if the mongos has been removed from the cluster.",
                    }
                )
            else:
                active_mongos.append(mongos["host"])

        if len(active_mongos) == 0:
            test_result.append(
                {
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": "No Active Mongos",
                    "description": "No active mongos found in the cluster.",
                }
            )
        if len(active_mongos) == 1:
            test_result.append(
                {
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": "Single Mongos",
                    "description": f"Only one mongos `{active_mongos[0]}` is available in the cluster. No failover is possible.",
                }
            )
        self.append_test_results(test_result)
        raw_result = {
            mongos["host"]: {
                "pingLatencySec": mongos["pingLatencySec"],
                "lastPing": mongos["lastPing"],
            }
            for mongos in all_mongos
        }
        return test_result, raw_result

    def _check_rs_member(self, set_name, node, **kwargs):
        """
        Run the replica set member level checks
        """
        test_result = []
        client = node["client"]
        latency = node.get("pingLatencySec", 0)
        if latency > MAX_MONGOS_PING_LATENCY:
            self._logger.warning(
                yellow(f"Skip {node['host']} because it has been irresponsive for {latency / 60:.2f} minutes.")
            )
            return None, None
        # Gather oplog information
        stats = client.local.command("collStats", "oplog.rs")
        server_status = client.admin.command("serverStatus")
        configured_retention_hours = server_status.get("oplogTruncation", {}).get("oplogMinRetentionHours", 0)
        latest_oplog = list(client.local.oplog.rs.find().sort("$natural", -1).limit(1))[0]["ts"]
        earliest_oplog = list(client.local.oplog.rs.find().sort("$natural", 1).limit(1))[0]["ts"]
        delta = latest_oplog.time - earliest_oplog.time
        current_retention_hours = delta / 3600  # Convert seconds to hours
        oplog_window_threshold = self._config.get("oplog_window_hours", 48)

        # Check oplog information
        retention_hours = max(configured_retention_hours, current_retention_hours)
        if retention_hours < oplog_window_threshold:
            test_result.append(
                {
                    "host": node["host"],
                    "severity": SEVERITY.HIGH,
                    "title": "Oplog Window Too Small",
                    "description": f"`Replica set `{set_name}` member {node['host']}` oplog window is `{retention_hours}` hours, below the recommended minimum `{oplog_window_threshold}` hours.",
                }
            )

        self.append_test_results(test_result)

        return test_result, {
            "oplogInfo": {
                "oplogMinRetentionHours": configured_retention_hours,
                "currentRetentionHours": current_retention_hours,
                "oplogStats": {
                    "size": stats["size"],
                    "count": stats["count"],
                    "storageSize": stats["storageSize"],
                    "maxSize": stats["maxSize"],
                    "averageObjectSize": stats["avgObjSize"],
                },
            }
        }

    def test(self, *args, **kwargs):
        """
        Main test method to gather sharded cluster information.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        nodes = discover_nodes(client, parsed_uri)
        result = enum_all_nodes(
            nodes,
            func_rs_cluster=self._check_rs,
            func_sh_cluster=self._check_sh,
            func_rs_member=self._check_rs_member,
            func_shard=self._check_rs,
            func_shard_member=self._check_rs_member,
            func_config=self._check_rs,
            func_config_member=self._check_rs_member,
        )

        self.captured_sample = result

    @property
    def review_result(
        self,
    ):
        result = self.captured_sample
        data = []
        sh_overview = {
            "type": "table",
            "caption": "Sharded Cluster Overview",
            "columns": [
                {"name": "#Shards", "type": "integer"},
                {"name": "#Mongos", "type": "integer"},
                {"name": "#Active mongos", "type": "integer"},
            ],
            "rows": [],
        }
        rs_overview = {
            "type": "table",
            "caption": f"{'Components' if result['type'] == 'SH' else 'Replica Set'} Overview",
            "columns": [
                {"name": "Name", "type": "string"},
                {"name": "#Members", "type": "integer"},
                {"name": "#Voting Members", "type": "integer"},
                {"name": "#Arbiters", "type": "integer"},
                {"name": "#Hidden Members", "type": "integer"},
            ],
            "rows": [],
        }
        mongos_details = {
            "type": "table",
            "caption": "Component Details - `mongos`",
            "columns": [
                {"name": "Host", "type": "string"},
                {"name": "Ping Latency (sec)", "type": "integer"},
                {"name": "Last Ping", "type": "boolean"},
            ],
            "rows": [],
        }
        if result["type"] == "SH":
            data.append(sh_overview)
        data.append(rs_overview)
        if result["type"] == "SH":
            data.append(mongos_details)

        def func_sh(name, result, **kwargs):
            raw_result = result["rawResult"]
            if raw_result is None:
                mongos_details["rows"].append(["n/a", "n/a", "n/a"])
                return
            component_names = result["map"].keys()
            shards = sum(1 for name in component_names if name not in ["mongos", "config"])
            mongos = len(result["map"]["mongos"]["members"])
            active_mongos = 0
            for host, info in raw_result.items():
                ping_latency = info.get("pingLatencySec", 0)
                last_ping = info.get("lastPing", False)
                mongos_details["rows"].append([host, ping_latency, last_ping])
                if ping_latency < MAX_MONGOS_PING_LATENCY:
                    active_mongos += 1
            sh_overview["rows"].append([shards, mongos, active_mongos])

        def func_rs(set_name, result, **kwargs):
            raw_result = result["rawResult"]
            if raw_result is None:
                return
            repl_config = raw_result["replsetConfig"]["config"]
            members = repl_config["members"]
            num_members = len(members)
            num_voting = sum(1 for m in members if m["votes"] > 0)
            num_arbiters = sum(1 for m in members if m["arbiterOnly"])
            num_hidden = sum(1 for m in members if m["hidden"])
            rs_overview["rows"].append(
                [
                    escape_markdown(set_name),
                    num_members,
                    num_voting,
                    num_arbiters,
                    num_hidden,
                ]
            )
            oplog_info = {}
            for m in result["members"]:
                r_result = m.get("rawResult", {})
                if r_result is None:
                    oplog_info[m["host"]] = {
                        "min_retention_hours": "n/a",
                        "current_retention_hours": "n/a",
                    }
                else:
                    oplog_info[m["host"]] = {
                        "min_retention_hours": round(
                            r_result.get("oplogInfo", {}).get("oplogMinRetentionHours", 0),
                            2,
                        ),
                        "current_retention_hours": round(
                            r_result.get("oplogInfo", {}).get("currentRetentionHours", 0),
                            2,
                        ),
                    }

            repl_status = result["rawResult"]["replsetStatus"]
            latest_optime = max(m["optime"]["ts"] for m in repl_status["members"])
            member_delay = {m["name"]: (latest_optime.time - m["optime"]["ts"].time) for m in repl_status["members"]}
            table_details = {
                "type": "table",
                "caption": f"Component Details - `{set_name}`",
                "columns": [
                    {"name": "Host", "type": "string"},
                    {"name": "_id", "type": "integer"},
                    {"name": "Arbiter", "type": "boolean"},
                    {"name": "Build Indexes", "type": "boolean"},
                    {"name": "Hidden", "type": "boolean"},
                    {"name": "Priority", "type": "integer"},
                    {"name": "Votes", "type": "integer"},
                    {"name": "Configured Delay (sec)", "type": "integer"},
                    {"name": "Current Delay (sec)", "type": "integer"},
                    {"name": "Oplog Window Hours", "type": "integer"},
                ],
                "rows": [],
            }
            for m in members:
                member_host = m["host"]
                min_retention_hours = oplog_info[member_host]["min_retention_hours"]
                current_retention_hours = oplog_info[member_host]["current_retention_hours"]
                if min_retention_hours in [0, "n/a"]:
                    retention_hours = current_retention_hours
                else:
                    retention_hours = max(min_retention_hours, current_retention_hours)
                table_details["rows"].append(
                    [
                        member_host,
                        m["_id"],
                        m["arbiterOnly"],
                        m["buildIndexes"],
                        m["hidden"],
                        m["priority"],
                        m["votes"],
                        m.get("secondaryDelaySecs", m.get("slaveDelay", 0)),
                        (member_delay[member_host] if member_host in member_delay else "n/a"),
                        retention_hours,
                    ]
                )
            data.append(table_details)

        enum_result_items(
            result,
            func_sh_cluster=func_sh,
            func_rs_cluster=func_rs,
            func_shard=func_rs,
            func_config=func_rs,
        )
        return {"name": self.name, "description": self.description, "data": data}


def check_replset_status(replset_status, config):
    """
    Check the replica set status for any issues.
    """
    result = []
    # Find primary in members
    primary_member = next(iter(m for m in replset_status["members"] if m["state"] == 1), None)

    if not primary_member:
        result.append(
            {
                "host": "cluster",
                "severity": SEVERITY.HIGH,
                "title": "No Primary",
                "description": f"`{replset_status['set']}` does not have a primary.",
            }
        )

    # Check member states
    max_delay = config.get("replication_lag_seconds", 60)
    set_name = replset_status.get("set", "Unknown Set")
    for member in replset_status["members"]:
        # Check problematic states
        state = member["state"]
        host = member["name"]

        if state in [3, 6, 8, 9, 10]:
            result.append(
                {
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "Unhealthy Member",
                    "description": f"`{set_name}` member `{host}` is in `{MEMBER_STATE[state]}` state.",
                }
            )
        elif state in [0, 5]:
            result.append(
                {
                    "host": host,
                    "severity": SEVERITY.LOW,
                    "title": "Initializing Member",
                    "description": f"`{set_name}` member `{host}` is being initialized in `{MEMBER_STATE[state]}` state.",
                }
            )

        # Check replication lag
        if state == 2:  # SECONDARY
            p_time = primary_member["optime"]["ts"]
            s_time = member["optime"]["ts"]
            lag = s_time.time - p_time.time
            if lag >= max_delay:
                result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.HIGH,
                        "title": "High Replication Lag",
                        "description": f"`{set_name}` member `{host}` has a replication lag of `{lag}` seconds, which is greater than the configured threshold of `{max_delay}` seconds.",
                    }
                )

    return result


def check_replset_config(replset_config, config):
    """
    Check the replica set configuration for any issues.
    """
    result = []
    set_name = replset_config["config"]["_id"]
    # Check number of voting members
    voting_members = sum(1 for member in replset_config["config"]["members"] if member.get("votes", 0) > 0)
    if voting_members < 3:
        result.append(
            {
                "host": "cluster",
                "severity": SEVERITY.HIGH,
                "title": "Insufficient Voting Members",
                "description": f"`{set_name}` has only {voting_members} voting members. Consider adding more to ensure fault tolerance.",
            }
        )
    if voting_members % 2 == 0:
        result.append(
            {
                "host": "cluster",
                "severity": SEVERITY.HIGH,
                "title": "Even Voting Members",
                "description": f"`{set_name}` has an even number of voting members, which can lead to split-brain scenarios. Consider adding an additional member.",
            }
        )

    for member in replset_config["config"]["members"]:
        if member.get("slaveDelay", 0) > 0:
            if member.get("votes", 0) > 0:
                result.append(
                    {
                        "host": member["host"],
                        "severity": SEVERITY.HIGH,
                        "title": "Delayed Voting Member",
                        "description": f"`{set_name}` member `{member['host']}` is a delayed secondary but is also a voting member. This can lead to performance issues.",
                    }
                )
            elif member.get("priority", 0) > 0:
                result.append(
                    {
                        "host": member["host"],
                        "severity": SEVERITY.HIGH,
                        "title": "Delayed Voting Member",
                        "description": f"`{set_name}` member `{member['host']}` is a delayed secondary but is has non-zero priority. This can lead to potential issues.",
                    }
                )
            elif not member.get("hidden", False):
                result.append(
                    {
                        "host": member["host"],
                        "severity": SEVERITY.MEDIUM,
                        "title": "Delayed Voting Member",
                        "description": f"`{set_name}` member `{member['host']}` is a delayed secondary and should be configured as hidden.",
                    }
                )
            else:
                result.append(
                    {
                        "host": member["host"],
                        "severity": SEVERITY.LOW,
                        "title": "Delayed Voting Member",
                        "description": f"`{set_name}` member `{member['host']}` is a delayed secondary. Delayed secondaries are not recommended in general.",
                    }
                )
        if member.get("arbiterOnly", False):
            result.append(
                {
                    "host": member["host"],
                    "severity": SEVERITY.HIGH,
                    "title": "Arbiter Member",
                    "description": f"`{set_name}` member `{member['host']}` is an arbiter. Arbiters are not recommended.",
                }
            )
    return result
