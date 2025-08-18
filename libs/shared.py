from enum import Enum
import re
from bson import json_util
import logging
import urllib.parse
from libs.utils import *
from pymongo.uri_parser import parse_uri
from pymongo import MongoClient
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
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

MAX_MONGOS_PING_LATENCY = 60  # seconds
RESERVED_CONN_OPTIONS = [
    "tls",
    "ssl",
    "authSource",
    "tlsCAFile",
    "tlsCertificateKeyFile",
    "tlsCertificateKeyFilePassword",
    "tlsAllowInvalidCertificates",
    "tlsAllowInvalidHostnames",
    "tlsInsecure",
    "connectTimeoutMS",
    "socketTimeoutMS"
]

def to_json(obj, indent=0):
    if env == "development":
        indent = 2
    def custom_json_serialize(obj):
        if isinstance(obj, SEVERITY):
            return obj.name
        else:
            return json_util._json_convert(obj)
    return json_util.dumps(obj, default=custom_json_serialize, indent=indent)

def to_markdown_id(str):
    id = str.lower()
    id = id.replace(' ', '-')
    id = re.sub(r'[^a-z0-9\-]', '', id)
    id = re.sub(r'\-+', '-', id)
    id = id.strip('-')
    return id

nodes = {}
def discover_nodes(client, parsed_uri):
    """
    Discover nodes in the MongoDB replica set or sharded cluster.
    For examples of discovered nodes, check out the `example_data_structure/discovered_rs.json,discovered_sh.json`.
    """
    global nodes
    if len(nodes) > 0:
        return nodes
    try:
        is_master = client.admin.command("isMaster")
        database = parsed_uri["database"] if parsed_uri.get("database", None) is not None else "test"
        # Reserve the options in the list
        options = []
        for k, v in parsed_uri["options"].items():
            if k in RESERVED_CONN_OPTIONS:
                options.append(f"{k}={str(v).lower() if isinstance(v, bool) else v}")
        options_str = "&".join(options)
        options_str_direct = "&".join(options + ["directConnection=true"])
        if parsed_uri.get("username") and parsed_uri.get("password"):
            credential = f"{parsed_uri['username']}:{urllib.parse.quote(parsed_uri['password'])}@"
        else:
            credential = ""
        if is_master.get("setName"):
            # Discover replica set nodes
            nodes["type"] = "RS"
            nodes["setName"] = is_master["setName"]
            hosts = [f"{host[0]}:{host[1]}" for host in parsed_uri['nodelist']]
            nodes["uri"] = f"mongodb://{credential}{','.join(hosts)}/{database}?{options_str}"
            nodes["client"] = MongoClient(nodes["uri"])
            members = client.admin.command("replSetGetStatus")["members"]

            # Prepare the nodes information
            nodes["members"] = []
            for member in members:
                uri = f"mongodb://{credential}{member['name']}/{database}?{options_str_direct}"
                nodes["members"].append({
                    "host": member["name"],
                    "uri": uri,
                    "client": MongoClient(uri)
                })
        else:
            # Discover sharded cluster nodes, including config servers and shards
            nodes["type"] = "SH"
            hosts = [f"{host[0]}:{host[1]}" for host in parsed_uri['nodelist']]
            nodes["uri"] = f"mongodb://{credential}{','.join(hosts)}/{database}?{options_str}"
            nodes["client"] = MongoClient(nodes["uri"])
            shard_map = client.admin.command("getShardMap")["map"]
            parsed_map = {}
            # config and shard nodes
            for k, v in shard_map.items():
                rs_name = v.split("/")[0]
                hosts = v.split("/")[1].split(",")
                uri = f"mongodb://{credential}{','.join(hosts)}/{database}?{options_str}"
                parsed_map[k] = {
                    "setName": rs_name,
                    "uri": uri,
                    "client": MongoClient(uri),
                    "members": []
                }
                for host in hosts:
                    uri = f"mongodb://{credential}{host}/{database}?{options_str_direct}"
                    parsed_map[k]["members"].append({
                        "host": host,
                        "uri": uri,
                        "client": MongoClient(uri)
                    })
            # mongos nodes
            all_mongos = list(client.config.get_collection("mongos").find())
            uri = f"mongodb://{credential}{','.join(host['_id'] for host in all_mongos)}/{database}?{options_str}"
            parsed_map["mongos"] = {
                "setName": "mongos",
                "uri": uri,
                "members": []
            }
            for host in all_mongos:
                ping = host.get("ping", datetime.now()).replace(tzinfo=timezone.utc)
                uri = f"mongodb://{credential}{host['_id']}/{database}?{options_str_direct}"
                latency = round((datetime.now(timezone.utc) - ping).total_seconds())
                parsed_map["mongos"]["members"].append({
                    "host": host["_id"],
                    "uri": uri,
                    "client": MongoClient(uri) if latency < MAX_MONGOS_PING_LATENCY else None,
                    "pingLatencySec": latency,
                    "lastPing": ping
                })
            nodes["map"] = parsed_map

    except Exception as e:
        logger.error(red(f"Failed to discover nodes: {str(e)}"))
        raise e

    return nodes

def enum_all_nodes(nodes, **kwargs):
    """
    Enumerate all nodes in the cluster and apply the provided functions.
    - `func_rs_cluster`: Function to apply to a replica set cluster.
    - `func_rs_member`: Function to apply to each replica set member.
    - `func_sh_cluster`: Function to apply to a sharded cluster.
    - `func_all_mongos`: Function to apply to all mongos nodes. This is generally the same as `func_sh_cluster`, but with all discovered mongos nodes included.
    - `func_mongos_member`: Function to apply to each mongos node.
    - `func_shard`: Function to apply to each shard.
    - `func_shard_member`: Function to apply to each shard member.
    - `func_config`: Function to apply to the CSRS.
    - `func_config_member`: Function to apply to each config member.

    Each function above will be passed 2 arguments: 
    - `set_name`: The replica set name if it's a replica set. Or "mongos" if it's a mongos node or sharded cluster.
    - `node`: The node information from `discover_nodes` output. Only the current and sub levels will be passed.
    - Named argument `level`: The level of the node in the cluster hierarchy (e.g., "sh_cluster", "rs_cluster", "rs_member").

    And is expected to return a Tuple:
    - `test_result`: The problems found.
    - `raw_result`: The raw data you captured, from which you get the `test_result`.

    Returns:
    A dictionary containing the results of applying the functions to the nodes. The returned structure will be similar to the discovered structure,
    to reflect the structure of the cluster. For example results, check out the `example_data_structure/result-rs.json,result-sh.json`.
    """
    func_rs_cluster = kwargs.get("func_rs_cluster", lambda s, n, **kwargs: (None, None))
    func_rs_member = kwargs.get("func_rs_member", lambda s, n, **kwargs: (None, None))
    func_sh_cluster = kwargs.get("func_sh_cluster", lambda s, n, **kwargs: (None, None))
    func_all_mongos = kwargs.get("func_all_mongos", lambda s, n, **kwargs: (None, None))
    func_mongos_member = kwargs.get("func_mongos_member", lambda s, n, **kwargs: (None, None))
    func_shard = kwargs.get("func_shard", lambda s, n, **kwargs: (None, None))
    func_shard_member = kwargs.get("func_shard_member", lambda s, n, **kwargs: (None, None))
    func_config = kwargs.get("func_config", lambda s, n, **kwargs: (None, None))
    func_config_member = kwargs.get("func_config_member", lambda s, n, **kwargs: (None, None))
    result = {
        "type": nodes["type"]
    }
    if nodes["type"] == "RS":
        set_name = nodes["setName"]
        result["setName"] = set_name
        result["members"] = []
        try:
            result["testResult"], result["rawResult"] = func_rs_cluster(set_name, nodes, level="rs_cluster")
        except Exception as e:
            logger.error(red(f"Failed to get execution result from replica set {set_name}: {e.__class__.__name__} {str(e)}"))
            result["testResult"], result["rawResult"] = (None, None)
        for member in nodes["members"]:
            test_result, raw_result = None, None
            try:
                test_result, raw_result = func_rs_member(set_name, member, level="rs_member")
            except Exception as e:
                logger.error(red(f"Failed to get execution result from replica set {set_name}, member {member['host']}: {e.__class__.__name__} {str(e)}"))

            result["members"].append({
                "host": member["host"],
                "rawResult": raw_result,
                "testResult": test_result
            })
    else:
        result["map"] = {}
        test_result, raw_result = None, None
        try:
            test_result, raw_result = func_sh_cluster("mongos", nodes, level="sh_cluster")
            result["testResult"], result["rawResult"] = test_result, raw_result
        except Exception as e:
            logger.error(red(f"Failed to get execution result from sharded cluster: {e.__class__.__name__} {str(e)}"))
        for component_name, host_info in nodes["map"].items():
            set_name = host_info["setName"]
            result["map"][component_name] = {
                "setName": host_info["setName"],
                "members": [],
                "rawResult": None,
                "testResult": None
            }
            test_result, raw_result = None, None
            try:
                if component_name == "mongos":
                    test_result, raw_result = func_all_mongos(set_name, host_info, level="all_mongos")
                elif component_name == "config":
                    test_result, raw_result = func_config(set_name, host_info, level="config")
                else:
                    test_result, raw_result = func_shard(set_name, host_info, level="shard")
                result["map"][component_name]["testResult"] = test_result
                result["map"][component_name]["rawResult"] = raw_result
            except Exception as e:
                logger.error(red(f"Failed to get execution result from {set_name}: {e.__class__.__name__} {str(e)}"))

            for member in host_info["members"]:
                test_result, raw_result = None, None
                try:
                    if component_name == "mongos":
                        test_result, raw_result = func_mongos_member(set_name, member, level="mongos_member")
                    elif component_name == "config":
                        test_result, raw_result = func_config_member(set_name, member, level="config_member")
                    else:
                        test_result, raw_result = func_shard_member(set_name, member, level="shard_member")
                except Exception as e:
                    logger.error(red(f"Failed to get execution result from {set_name}, member {member['host']}: {e.__class__.__name__} {str(e)}"))

                result["map"][component_name]["members"].append({
                    "host": member["host"],
                    "rawResult": raw_result,
                    "testResult": test_result
                })
    return result

def enum_result_items(result, **kwargs):
    """
    Enumerate all results and apply the provided functions. The result will be passed to the following functions.
    - `func_rs_cluster`: Handle replica set cluster level results.
    - `func_rs_member`: Handle replica set member level results.
    - `func_sh_cluster`: Handle sharded cluster level results.
    - `func_all_mongos`: Handle all mongos level results.
    - `func_mongos_member`: Handle each mongos member level results.
    - `func_shard`: Handle each shard level results.
    - `func_shard_member`: Handle each shard member level results.
    - `func_config`: Handle the CSRS level results.
    - `func_config_member`: Handle each config member level results.

    Arguments passed to the functions:
    - `set_name`: The replica set name if it's a replica set. Or "mongos" if it's a mongos node or sharded cluster.
    - `node`: The node information, including the results, from `discover_nodes` output.
    - Named argument `level`: The level of the node in the cluster hierarchy (e.g., "sh_cluster", "rs_cluster", "rs_member").

    Returns:
    Nothing returned.
    """
    func_rs_cluster = kwargs.get("func_rs_cluster", lambda s, n, **kwargs: None)
    func_rs_member = kwargs.get("func_rs_member", lambda s, n, **kwargs: None)
    func_sh_cluster = kwargs.get("func_sh_cluster", lambda s, n, **kwargs: None)
    func_all_mongos = kwargs.get("func_all_mongos", lambda s, n, **kwargs: None)
    func_mongos_member = kwargs.get("func_mongos_member", lambda s, n, **kwargs: None)
    func_shard = kwargs.get("func_shard", lambda s, n, **kwargs: None)
    func_shard_member = kwargs.get("func_shard_member", lambda s, n, **kwargs: None)
    func_config = kwargs.get("func_config", lambda s, n, **kwargs: None)
    func_config_member = kwargs.get("func_config_member", lambda s, n, **kwargs: None)
    if result["type"] == "RS":
        func_rs_cluster(result["setName"], result, level="rs_cluster")
        for member in result["members"]:
            func_rs_member(result["setName"], member, level="rs_member")
    else:
        func_sh_cluster("mongos", result, level="sh_cluster")
        for component_name, host_info in result["map"].items():
            set_name = host_info["setName"]
            if set_name == "mongos":
                func_all_mongos(set_name, host_info, level="all_mongos")
            elif set_name == "config":
                func_config(set_name, host_info, level="config")
            else:
                func_shard(set_name, host_info, level="shard")
            for member in host_info["members"]:
                if component_name == "mongos":
                    func_mongos_member(set_name, member, level="mongos_member")
                elif component_name == "config":
                    func_config_member(set_name, member, level="config_member")
                else:
                    func_shard_member(set_name, member, level="shard_member")

def format_size(bytes, decimal=2):
    """
    Format the size in bytes to a human-readable string.

    Args:
        bytes (int): The size in bytes.
        decimal (int): The number of decimal places to include.

    Returns:
        str: The formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024:
            return f"{bytes:.{decimal}f} {unit}"
        bytes /= 1024
    return f"{bytes:.{decimal}f} PB"

if __name__ == "__main__":
    from bson import json_util
    parsed_uri = parse_uri("mongodb://localhost:30017?tls=false")
    client = MongoClient("mongodb://localhost:30017?tls=false")
    nodes = discover_nodes(client, parsed_uri)
    result = enum_all_nodes(nodes, lambda s, n: {"setName": s, "uri": n["uri"]}, lambda s, n: {"setName": s, "host": n["host"]})
    print(json_util.dumps(result, indent=2))