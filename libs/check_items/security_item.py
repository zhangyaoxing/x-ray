from pymongo import MongoClient
from libs.check_items.base_item import BaseItem
from libs.shared import MAX_MONGOS_PING_LATENCY, SEVERITY, discover_nodes, enum_all_nodes
from libs.utils import *

class SecurityItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Authentication & Security"
        self._description = "Collects & review security related information."

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering security information...")
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
            if port == 27017:
                test_result.append({
                    "host": host,
                    "severity": SEVERITY.LOW,
                    "title": "Default Port Used",
                    "description": "Default port `27017` is used, which may expose the server to unnecessary risks."
                })
            self.append_test_results(test_result)

            return test_result, raw_result

        result = enum_all_nodes(nodes, func_rs_member=func_node, func_mongos=func_node)

        self.captured_sample = result