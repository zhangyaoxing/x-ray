"""
This module defines a checklist item for collecting and reviewing security-related information in MongoDB.
"""

from libs.healthcheck.check_items.base_item import BaseItem
from libs.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    discover_nodes,
    enum_all_nodes,
    enum_result_items,
    SEVERITY,
)
from libs.utils import yellow, escape_markdown


class SecurityItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Authentication & Security"
        self._description = "Collects & review security related information.\n\n"
        self._description += "- Whether authorization is enabled.\n"
        self._description += "- Whether log redaction is enabled.\n"
        self._description += "- Whether TLS is enabled and required.\n"
        self._description += "- Whether the bind IP is too permissive.\n"
        self._description += "- Whether the default port is used.\n"
        self._description += "- Whether auditing is enabled.\n"
        self._description += "- Whether encryption at rest is enabled.\n"

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        nodes = discover_nodes(client, parsed_uri)

        def func_node(name, node, **kwargs):
            client = node["client"]
            host = node["host"]
            if (
                "pingLatencySec" in node
                and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY
            ):
                self._logger.warning(
                    yellow(
                        f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            raw_result = client.admin.command("getCmdLineOpts")
            test_result = []

            # Check for security settings
            parsed = raw_result.get("parsed", {})
            security_settings = parsed.get("security", {})
            net = parsed.get("net", {})
            audit_log = parsed.get("auditLog", {})
            authorization = security_settings.get("authorization", None)
            redact_logs = security_settings.get("redactClientLogData", None)
            bind_ip = net.get("bindIp", "127.0.0.1")
            port = net.get("port", None)
            tls_enabled = net.get("tls", {}).get("mode", None)
            audit = (
                "enabled"
                if audit_log.get("destination", None) is not None
                else "disabled"
            )
            if authorization != "enabled":
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.HIGH,
                        "title": "Authorization Disabled",
                        "description": "Authorization is disabled, which may lead to unauthorized access.",
                    }
                )
            if not redact_logs:
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.MEDIUM,
                        "title": "Log Redaction Disabled",
                        "description": "Redaction of log is disabled, which may lead to sensitive information exposure.",
                    }
                )
            if tls_enabled is None:
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.HIGH,
                        "title": "TLS Disabled",
                        "description": "TLS is disabled, which may lead to unencrypted connections.",
                    }
                )
            elif tls_enabled != "requireTLS":
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.MEDIUM,
                        "title": "Optional TLS",
                        "description": f"TLS is enabled but not set to `requireTLS`, current mode is `{tls_enabled}`.",
                    }
                )
            if bind_ip == "0.0.0.0":
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.LOW,
                        "title": "Unrestricted Bind IP",
                        "description": "Bind IP is set to `0.0.0.0`. Your service may be exposed to the internet. Make sure to restrict it to specific IP addresses.",
                    }
                )
            if port == 27017:
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.LOW,
                        "title": "Default Port Used",
                        "description": "Default port `27017` is used. Make sure to restrict access to this port.",
                    }
                )

            if audit == "disabled":
                test_result.append(
                    {
                        "host": host,
                        "severity": SEVERITY.HIGH,
                        "title": "Auditing Disabled",
                        "description": "Auditing is disabled, which may lead to unmonitored access.",
                    }
                )
            self.append_test_results(test_result)

            return test_result, raw_result

        result = enum_all_nodes(
            nodes,
            func_rs_member=func_node,
            func_mongos_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )

        self.captured_sample = result

    @property
    def review_result(self):
        raw_result = self.captured_sample
        table = {
            "type": "table",
            "caption": "Security Information",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Listen", "type": "string"},
                {"name": "TLS", "type": "string"},
                {"name": "Authorization", "type": "string"},
                {"name": "Cluster Auth", "type": "string"},
                {"name": "Log Redaction", "type": "string"},
                {"name": "EAR", "type": "string"},
                {"name": "Auditing", "type": "string"},
            ],
            "rows": [],
        }

        def func_node(name, node, **kwargs):
            raw_result = node["rawResult"]
            host = node["host"]
            if raw_result is None:
                table["rows"].append(
                    [
                        escape_markdown(name),
                        host,
                        "n/a",
                        "n/a",
                        "n/a",
                        "n/a",
                        "n/a",
                        "n/a",
                        "n/a",
                    ]
                )
                return

            parsed = raw_result.get("parsed", {})
            net = parsed.get("net", {})
            security = parsed.get("security", {})
            audit_log = parsed.get("auditLog", {})
            port = net.get("port", 27017)
            tls = net.get("tls", {}).get("mode", "disabled")
            authorization = security.get("authorization", "disabled")
            log_redaction = security.get("redactClientLogData", "disabled")
            eat = security.get("enableEncryption", "false")
            bind_ip = net.get("bindIp", "127.0.0.1")
            cluster_auth = security.get("clusterAuthMode", "disabled")
            audit = (
                "enabled"
                if audit_log.get("destination", None) is not None
                else "disabled"
            )
            table["rows"].append(
                [
                    escape_markdown(name),
                    host,
                    f"{bind_ip}:{port}",
                    tls,
                    authorization,
                    cluster_auth,
                    log_redaction,
                    eat,
                    audit,
                ]
            )

        enum_result_items(
            raw_result,
            func_rs_member=func_node,
            func_mongos_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )

        return {"name": self.name, "description": self.description, "data": [table]}
