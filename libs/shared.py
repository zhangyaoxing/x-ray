import logging
import urllib.parse
from libs.utils import *
from pymongo.uri_parser import parse_uri

logger = logging.getLogger(__name__)
SOCKET_TIMEOUT_MS = 5000
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
                "uri": f"mongodb://{credential}{m['name']}/?authSource={auth_source}&directConnection=true&socketTimeoutMS={SOCKET_TIMEOUT_MS}",
            } for m in members]
        else:
            # Discover sharded cluster nodes, including config servers and shards
            nodes["type"] = "SH"
            shard_map = client.admin.command("getShardMap")["map"]
            parsed_map = {}
            for k, v in shard_map.items():
                rs_name = v.split("/")[0]
                hosts = v.split("/")[1].split(",")
                parsed_map[k] = {
                    "setName": rs_name,
                    "uri": f"mongodb://{credential}{'_'.join(hosts)}/?authSource={auth_source}&socketTimeoutMS={SOCKET_TIMEOUT_MS}",
                    "hosts": [{
                        "host": host,
                        "uri": f"mongodb://{credential}{host}/?authSource={auth_source}&directConnection=true&socketTimeoutMS={SOCKET_TIMEOUT_MS}"
                    } for host in hosts]
                }
            active_mongos = list(client.config.get_collection("mongos").find())
            nodes["mongos"] = [{
                "host": host["_id"],
                "uri": f"mongodb://{credential}{host['_id']}/?authSource={auth_source}&socketTimeoutMS={SOCKET_TIMEOUT_MS}"
            } for host in active_mongos]
            nodes["map"] = parsed_map

    except Exception as e:
        logger.error(red(f"Failed to discover nodes: {str(e)}"))
        raise e

    return nodes

if __name__ == "__main__":
    from pymongo import MongoClient
    parsed_uri = parse_uri("mongodb://localhost:30017")
    client = MongoClient("mongodb://localhost:30017")
    nodes = discover_nodes(client, parsed_uri)
    for node in nodes:
        print(node)