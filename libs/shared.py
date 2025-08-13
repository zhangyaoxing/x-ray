from enum import Enum
import logging
import urllib.parse
from libs.utils import *
from pymongo.uri_parser import parse_uri
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
CONNECT_TIMEOUT_MS = 5000
MEMBER_STATE = {
    0: "STARTUP",
    1: "PRIMARY",
    2: "SECONDARY",
    3: "RECOVERING",
    5: "STARTUP2",
    6: "UNKNOWN",
    7: "ARBITER",
    8: "DOWN",
    9: "ROLLBACK",
    10: "REMOVED"
}
class SEVERITY(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4

def discover_nodes(client, parsed_uri):
    """
    Discover nodes in the MongoDB replica set or sharded cluster.
    """
    nodes = {}
    try:
        is_master = client.admin.command("isMaster")
        auth_source = parsed_uri['options'].get('authSource', 'admin')
        if parsed_uri.get("username") and parsed_uri.get("password"):
            credential = f"{parsed_uri['username']}:{urllib.parse.quote(parsed_uri['password'])}@"
        else:
            credential = ""
        if is_master.get("setName"):
            # Discover replica set nodes
            nodes["type"] = "RS"
            nodes["setName"] = is_master["setName"]
            members = client.admin.command("replSetGetStatus")["members"]

            # Prepare the nodes information
            nodes["members"] = [{
                "host": m["name"], 
                "uri": f"mongodb://{credential}{m['name']}/?authSource={auth_source}&directConnection=true&connectTimeoutMS={CONNECT_TIMEOUT_MS}",
            } for m in members]
        else:
            # Discover sharded cluster nodes, including config servers and shards
            nodes["type"] = "SH"
            shard_map = client.admin.command("getShardMap")["map"]
            parsed_map = {}
            # config and shard nodes
            for k, v in shard_map.items():
                rs_name = v.split("/")[0]
                hosts = v.split("/")[1].split(",")
                parsed_map[k] = {
                    "setName": rs_name,
                    "uri": f"mongodb://{credential}{','.join(hosts)}/?authSource={auth_source}&connectTimeoutMS={CONNECT_TIMEOUT_MS}",
                    "hosts": [{
                        "host": host,
                        "uri": f"mongodb://{credential}{host}/?authSource={auth_source}&directConnection=true&connectTimeoutMS={CONNECT_TIMEOUT_MS}"
                    } for host in hosts]
                }
            nodes["map"] = parsed_map
            # mongos nodes
            all_mongos = list(client.config.get_collection("mongos").find())
            nodes["mongos"] = []
            for host in all_mongos:
                ping = host.get("ping", datetime.now()).replace(tzinfo=timezone.utc)
                nodes["mongos"].append({
                    "host": host["_id"],
                    "uri": f"mongodb://{credential}{host['_id']}/?authSource={auth_source}&connectTimeoutMS={CONNECT_TIMEOUT_MS}",
                    "pingLatencySec": (datetime.now(timezone.utc) - ping).total_seconds()
                })

    except Exception as e:
        logger.error(red(f"Failed to discover nodes: {str(e)}"))
        raise e

    return nodes

def check_replset_status(replset_status, config):
    """
    Check the replica set status for any issues.
    """
    result = []
    # Find primary in members
    primary_member = next(iter(m for m in replset_status["members"] if m["state"] == 1), None)

    if not primary_member:
        result.append({
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
                "severity": SEVERITY.HIGH,
                "title": "Unhealthy Member",
                "description": f"`{set_name}` member `{host}` is in `{MEMBER_STATE[state]}` state."
            })
        elif state in [0, 5]:
            result.append({
                "severity": SEVERITY.LOW,
                "title": "Initializing Member",
                "description": f"`{set_name}` member `{host}` is being initialized in `{MEMBER_STATE[state]}` state."
            })

        # Check replication lag
        if state == 2:  # SECONDARY
            lag = member["optimeDate"] - primary_member["optimeDate"]
            if lag.seconds >= max_delay:
                result.append({
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
            "severity": SEVERITY.HIGH,
            "title": "Insufficient Voting Members",
            "description": f"`{set_name}` has only {voting_members} voting members. Consider adding more to ensure fault tolerance."
        })
    if voting_members % 2 == 0:
        result.append({
            "severity": SEVERITY.HIGH,
            "title": "Even Voting Members",
            "description": f"`{set_name}` has an even number of voting members, which can lead to split-brain scenarios. Consider adding an additional member."
        })

    for member in replset_config["config"]["members"]:
        if member.get("slaveDelay", 0) > 0:
            if member.get("votes", 0) > 0:
                result.append({
                    "severity": SEVERITY.HIGH,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary but is also a voting member. This can lead to performance issues."
                })
            elif member.get("priority", 0) > 0:
                result.append({
                    "severity": SEVERITY.HIGH,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary but is has non-zero priority. This can lead to potential issues."
                })
            elif not member.get("hidden", False):
                result.append({
                    "severity": SEVERITY.MEDIUM,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary and should be configured as hidden."
                })
            else:
                result.append({
                    "severity": SEVERITY.LOW,
                    "title": "Delayed Voting Member",
                    "description": f"`{set_name}` member `{member['host']}` is a delayed secondary. Delayed secondaries are not recommended in general."
                })
        if member.get("arbiterOnly", False):
            result.append({
                "severity": SEVERITY.HIGH,
                "title": "Arbiter Member",
                "description": f"`{set_name}` member `{member['host']}` is an arbiter. Arbiters are not recommended."
            })
    return result

def check_oplog_window(nodes, config):
    """
    Check the oplog window for each replica set member.
    """
    result = []
    raw = []
    max_oplog_window = config.get("oplog_window_hours", 48)
    for node in nodes["members"]:
        client = MongoClient(node["uri"], serverSelectionTimeoutMS=CONNECT_TIMEOUT_MS)
        try:
            oplog_info = gather_oplog_info(client)
            raw.append({node["host"]: oplog_info})
            retention_hours = oplog_info.get("retentionHours", 0)
            if retention_hours < max_oplog_window:
                result.append({
                    "severity": SEVERITY.HIGH,
                    "title": "Oplog Window Too Small",
                    "description": f"`{node['host']}` oplog window is {retention_hours} hours, below the recommended minimum {max_oplog_window} hours."
                })
            
        except Exception as e:
            logger.error(red(f"Failed to check oplog window for `{node['host']}`: {str(e)}"))
            
    return raw, result
def gather_replset_info(client):
    """
    Gather replica set configuration and status.
    """
    try:
        is_master = client.admin.command("isMaster")
        if not is_master.get("setName"):
            logger.warning(yellow("This MongoDB instance is not part of a replica set. Skipping..."))
            return None, None
        replset_status = client.admin.command("replSetGetStatus")
        replset_config = client.admin.command("replSetGetConfig")
        return replset_status, replset_config
    except OperationFailure as e:
        logger.warning(yellow(f"Failed to gather replica set information: {str(e)}"))
        return None, None
    
def gather_oplog_info(client):
    """
    Gather oplog information.
    """
    try:
        stats = client.local.command("collStats", "oplog.rs")
        server_status = client.admin.command("serverStatus")
        if server_status.get("oplogTruncation", {}).get("minRetentionHours", None) is not None:
            retention_hours = server_status["oplogTruncation"]["minRetentionHours"]
        else:
            latest = list(client.local.oplog.rs.find().sort("$natural", -1).limit(1))[0]["ts"]
            earliest = list(client.local.oplog.rs.find().sort("$natural", 1).limit(1))[0]["ts"]
            delta = latest.time - earliest.time
            retention_hours = delta / 3600  # Convert seconds to hours
        return {
            "retentionHours": retention_hours,
            "oplogStats": stats
        }
    except Exception as e:
        logger.error(red(f"Failed to check oplog window for `{node['host']}`: {str(e)}"))
        return {}
    
if __name__ == "__main__":
    from pymongo import MongoClient
    parsed_uri = parse_uri("mongodb://localhost:30017")
    client = MongoClient("mongodb://localhost:30017")
    nodes = discover_nodes(client, parsed_uri)
    for node in nodes:
        print(node)