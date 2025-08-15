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
        raw_result = None
        replset_status = client.admin.command("replSetGetStatus")
        replset_config = client.admin.command("replSetGetConfig")

        # Check replica set status and config
        result = check_replset_status(replset_status, self._config)
        for item in result:
            self.append_item_result(item["host"], item["severity"], item["title"], item["description"])
        result = check_replset_config(replset_config, self._config)
        for item in result:
            self.append_item_result(item["host"], item["severity"], item["title"], item["description"])

        raw_result = {
            "replset_status": replset_status,
            "replset_config": replset_config,
        }
        return raw_result

    def _check_sh(self, set_name, node):
        """
        Check if the sharded cluster is available and connected.
        """
        raw_result = None
        all_mongos = node["map"]["mongos"]["members"]
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
                "cluster",
                SEVERITY.HIGH,
                "Single Mongos",
                f"Only one mongos `{active_mongos[0]}` is available in the cluster. No failover is possible."
            )
        raw_result = {
            mongos["host"]: {
                "pingLatencySec": mongos["pingLatencySec"]
            } for mongos in all_mongos
        }
        return raw_result

    def _check_rs_member(self, set_name, node):
        """
        Run the replica set member level checks
        """
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
            self.append_item_result(
                node["host"],
                SEVERITY.HIGH,
                "Oplog Window Too Small",
                f"`Replica set `{set_name}` member {node['host']}` oplog window is `{retention_hours}` hours, below the recommended minimum `{oplog_window_threshold}` hours."
            )

        return {
            "oplog_info": {
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
        sample_result = enum_all_nodes(nodes,
                                       func_rs=self._check_rs,
                                       func_sh=self._check_sh,
                                       func_rs_member=self._check_rs_member)

        self.captured_sample = sample_result



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