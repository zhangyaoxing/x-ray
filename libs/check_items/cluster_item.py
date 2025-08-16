from pymongo import MongoClient
from libs.check_items.base_item import BaseItem
from libs.shared import *
from libs.utils import *

class ClusterItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Sharded Cluster Information"
        self._description = "Collects and reviews sharded cluster configuration and status."

    def _check_rs(self, set_name, node):
        """
        Run the cluster level checks
        """
        client = node["client"]
        test_result= []
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

    def _check_sh(self, set_name, node):
        """
        Check if the sharded cluster is available and connected.
        """
        test_result = []
        all_mongos = node["map"]["mongos"]["members"]
        active_mongos = []
        for mongos in all_mongos:
            if mongos.get("pingLatencySec", 0) > MAX_MONGOS_PING_LATENCY:
                test_result.append({
                    "host": mongos["host"],
                    "severity": SEVERITY.LOW,
                    "title": "Irresponsive Mongos",
                    "description": f"Mongos `{mongos['host']}` is not responsive. Last ping was at `{round(mongos['pingLatencySec'])}` seconds ago. This is expected if the mongos has been removed from the cluster."
                })
            else:
                active_mongos.append(mongos["host"])

        if len(active_mongos) == 0:
            test_result.append({
                "host": "cluster",
                "severity": SEVERITY.HIGH,
                "title": "No Active Mongos",
                "description": "No active mongos found in the cluster."
            })
        if len(active_mongos) == 1:
            test_result.append({
                "host": "cluster",
                "severity": SEVERITY.HIGH,
                "title": "Single Mongos",
                "description": f"Only one mongos `{active_mongos[0]}` is available in the cluster. No failover is possible."
            })
        self.append_test_results(test_result)
        raw_result = {
            mongos["host"]: {
                "pingLatencySec": mongos["pingLatencySec"]
            } for mongos in all_mongos
        }
        return test_result, raw_result

    def _check_rs_member(self, set_name, node):
        """
        Run the replica set member level checks
        """
        test_result = []
        client = node["client"]
        # Gather oplog information
        stats = client.local.command("collStats", "oplog.rs")
        server_status = client.admin.command("serverStatus")
        configured_retention_hours = server_status.get("oplogTruncation", {}).get("minRetentionHours", 0)
        latest_oplog = list(client.local.oplog.rs.find().sort("$natural", -1).limit(1))[0]["ts"]
        earliest_oplog = list(client.local.oplog.rs.find().sort("$natural", 1).limit(1))[0]["ts"]
        delta = latest_oplog.time - earliest_oplog.time
        current_retention_hours = delta / 3600  # Convert seconds to hours
        oplog_window_threshold = self._config.get("oplog_window_hours", 48)

        # Check oplog information
        retention_hours = configured_retention_hours if configured_retention_hours > 0 else current_retention_hours
        if retention_hours < oplog_window_threshold:
            test_result.append({
                "host": node["host"],
                "severity": SEVERITY.HIGH,
                "title": "Oplog Window Too Small",
                "description": f"`Replica set `{set_name}` member {node['host']}` oplog window is `{retention_hours}` hours, below the recommended minimum `{oplog_window_threshold}` hours."
            })

        self.append_test_results(test_result)

        return test_result, {
            "oplogInfo": {
                "minRetentionHours": configured_retention_hours,
                "currentRetentionHours": current_retention_hours,
                "oplogStats": {
                    "size": stats["size"],
                    "count": stats["count"],
                    "storageSize": stats["storageSize"],
                    "maxSize": stats["maxSize"],
                    "averageObjectSize": stats["avgObjSize"],
                }
            }
        }

    def test(self, *args, **kwargs):
        """
        Main test method to gather sharded cluster information.
        """
        self._logger.info(f"Gathering sharded cluster info...")
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        nodes = discover_nodes(client, parsed_uri)
        execution_result = enum_all_nodes(nodes,
                                       func_rs_cluster=self._check_rs,
                                       func_sh_cluster=self._check_sh,
                                       func_rs_member=self._check_rs_member,
                                       func_shard=self._check_rs,
                                       func_shard_member=self._check_rs_member,
                                       func_config=self._check_rs,
                                       func_config_member=self._check_rs_member)

        self.captured_sample = execution_result

    @property
    def review_result(self, ):
        result = self.captured_sample
        data = []
        sh_overview = {
            "type": "table",
            "caption": f"Sharded Cluster Overview",
            "columns": [
                {"name": "Type", "type": "string"},
                {"name": "#Shards", "type": "integer"},
                {"name": "#Mongos", "type": "integer"},
            ],
            "rows": []
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
            "rows": []
        }
        data.append(sh_overview) if result["type"] == "SH" else None
        data.append(rs_overview)
        def func_sh(name, result):
            component_names = result["map"].keys()
            shards = sum(1 for name in component_names if name not in ["mongos", "config"])
            mongos = len(result["map"]["mongos"]["members"])
            sh_overview["rows"].append(["Sharded Cluster", shards, mongos])

        def func_rs(set_name, result):
            repl_status = result["rawResult"]["replsetConfig"]["config"]
            members = repl_status["members"]
            num_members = len(members)
            num_voting = sum(1 for m in members if m["votes"] > 0)
            num_arbiters = sum(1 for m in members if m["arbiterOnly"])
            num_hidden = sum(1 for m in members if m["hidden"])
            rs_overview["rows"].append([set_name, num_members, num_voting, num_arbiters, num_hidden])
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
                    {"name": "Delay", "type": "integer"}
                ],
                "rows": [
                    [m["host"], m["_id"], m["arbiterOnly"], m["buildIndexes"], m["hidden"], m["priority"], m["votes"], m.get("secondaryDelaySecs", m.get("slaveDelay", 0))] for m in members
                ]
            }
            data.append(table_details)

        enum_result_items(result, 
                          func_sh_cluster=func_sh, 
                          func_rs_cluster=func_rs,
                          func_shard=func_rs,
                          func_config=func_rs)
        return {
            "name": self.name,
            "description": self.description,
            "data": data
        }


def check_replset_status(replset_status, config):
    """
    Check the replica set status for any issues.
    """
    result = []
    # Find primary in members
    primary_member = next(iter(m for m in replset_status["members"] if m["state"] == 1), None)

    if not primary_member:
        result.append({
            "host": "cluster",
            "severity": SEVERITY.HIGH,
            "title": "No Primary",
            "description": f"`{replset_status['set']}` does not have a primary."
        })

    # Check member states
    max_delay = config.get("replication_lag_seconds", 60)
    set_name = replset_status.get("set", "Unknown Set")
    for member in replset_status["members"]:
        # Check problematic states
        state = member["state"]
        host = member["name"]
        
        if state in [3, 6, 8, 9, 10]:
            result.append({
                "host": host,
                "severity": SEVERITY.HIGH,
                "title": "Unhealthy Member",
                "description": f"`{set_name}` member `{host}` is in `{MEMBER_STATE[state]}` state."
            })
        elif state in [0, 5]:
            result.append({
                "host": host,
                "severity": SEVERITY.LOW,
                "title": "Initializing Member",
                "description": f"`{set_name}` member `{host}` is being initialized in `{MEMBER_STATE[state]}` state."
            })

        # Check replication lag
        if state == 2:  # SECONDARY
            lag = member["optimeDate"] - primary_member["optimeDate"]
            if lag.seconds >= max_delay:
                result.append({
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "High Replication Lag",
                    "description": f"`{set_name}` member `{host}` has a replication lag of `{lag.seconds}` seconds, which is greater than the configured threshold of `{max_delay}` seconds."
                })

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
        result.append({
            "host": "cluster",
            "severity": SEVERITY.HIGH,
            "title": "Insufficient Voting Members",
            "description": f"`{set_name}` has only {voting_members} voting members. Consider adding more to ensure fault tolerance."
        })
    if voting_members % 2 == 0:
        result.append({
            "host": "cluster",
            "severity": SEVERITY.HIGH,
            "title": "Even Voting Members",
            "description": f"`{set_name}` has an even number of voting members, which can lead to split-brain scenarios. Consider adding an additional member."
        })

    for member in replset_config["config"]["members"]:
        if member.get("slaveDelay", 0) > 0:
            if member.get("votes", 0) > 0:
                result.append({
                    "host": member["host"],
                    "severity": SEVERITY.HIGH,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary but is also a voting member. This can lead to performance issues."
                })
            elif member.get("priority", 0) > 0:
                result.append({
                    "host": member["host"],
                    "severity": SEVERITY.HIGH,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary but is has non-zero priority. This can lead to potential issues."
                })
            elif not member.get("hidden", False):
                result.append({
                    "host": member["host"],
                    "severity": SEVERITY.MEDIUM,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary and should be configured as hidden."
                })
            else:
                result.append({
                    "host": member["host"],
                    "severity": SEVERITY.LOW,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary. Delayed secondaries are not recommended in general."
                })
        if member.get("arbiterOnly", False):
            result.append({
                "host": member["host"],
                "severity": SEVERITY.HIGH,
                "title": "Arbiter Member",
                "description": f"`{set_name}` member `{member['host']}` is an arbiter. Arbiters are not recommended."
            })
    return result