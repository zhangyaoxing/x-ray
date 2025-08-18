from pymongo import MongoClient
from libs.check_items.base_item import BaseItem
from libs.shared import MAX_MONGOS_PING_LATENCY, SEVERITY, discover_nodes, enum_all_nodes, enum_result_items
from libs.utils import *

class SecurityItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Authentication & Security"
        self._description = "Collects & review security related information."

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        nodes = discover_nodes(client, parsed_uri)
        def func_node(name, node):
            client = node["client"]
            host = node["host"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(yellow(f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60} minutes."))
                return None, None
            raw_result = client.admin.command("getCmdLineOpts")
            test_result = []

            # Check for security settings
            security_settings = raw_result.get("parsed", {}).get("security", {})
            authorization = security_settings.get("authorization", None)
            redact_logs = security_settings.get("redactClientLogData", None)
            net = raw_result.get("parsed", {}).get("net", {})
            bind_ip = net.get("bindIp", "127.0.0.1")
            port = net.get("port", None)
            tls_enabled = net.get("tls", {}).get("mode", None)
            if authorization != "enabled":
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "Authorization Disabled",
                    "description": "Authorization is disabled, which may lead to unauthorized access."
                })
            if redact_logs != True:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "Log Redaction Disabled",
                    "description": "Redaction of log is disabled, which may lead to sensitive information exposure."
                })
            if tls_enabled is None:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "TLS Disabled",
                    "description": "TLS is disabled, which may lead to unencrypted connections."
                })
            elif tls_enabled != "requireTLS":
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.MEDIUM,
                    "title": "Optional TLS",
                    "description": f"TLS is enabled but not set to `requireTLS`, current mode is `{tls_enabled}`."
                })
            if bind_ip == "0.0.0.0":
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.HIGH,
                    "title": "Unrestricted Bind IP",
                    "description": "Bind IP is set to `0.0.0.0`, which may expose the server to unauthorized access."
                })
            if port == 27017:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.LOW,
                    "title": "Default Port Used",
                    "description": "Default port `27017` is used, which may expose the server to unnecessary risks."
                })
            self.append_test_results(test_result)

            return test_result, raw_result

        result = enum_all_nodes(nodes, 
                                func_rs_member=func_node, 
                                func_mongos_member=func_node,
                                func_shard_member=func_node,
                                func_config_member=func_node)

        self.captured_sample = result

    @property
    def review_result(self):
        raw_result = self.captured_sample
        table = {
            "type": "table",
            "caption": f"Security Information",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Listen", "type": "string"},
                {"name": "TLS", "type": "string"},
                {"name": "Authorization", "type": "string"},
                {"name": "Cluster Auth", "type": "string"},
                {"name": "Log Redaction", "type": "string"},
                {"name": "EAT", "type": "boolean"}
            ],
            "rows": []
        }
        def func_node(name, node):
            raw = node["rawResult"]
            if raw is None:
                return

            host = node["host"]
            net = raw.get("parsed", {}).get("net", {})
            security = raw.get("parsed", {}).get("security", {})
            port = net.get("port", 27017)
            tls = net.get("tls", {}).get("mode", "disabled")
            authorization = security.get("authorization", "disabled")
            log_redaction = security.get("redactClientLogData", "disabled")
            eat = security.get("enableEncryption", "false")
            bind_ip = net.get("bindIp", "127.0.0.1")
            cluster_auth = security.get("clusterAuthMode", "disabled")
            table["rows"].append([name, host, f"{bind_ip}:{port}", tls, authorization, cluster_auth, log_redaction, eat])

        enum_result_items(raw_result,
                          func_rs_member=func_node,
                          func_mongos_member=func_node,
                          func_shard_member=func_node,
                          func_config_member=func_node)

        return {
            "name": self.name,
            "description": self.description,
            "data": [table]
        }