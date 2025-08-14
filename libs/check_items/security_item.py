from pymongo import MongoClient
from libs.check_items.base_item import BaseItem
from libs.shared import SEVERITY
from libs.utils import *

class SecurityItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Authentication & Security"
        self._description = "Collects & review security related information."

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering security information...")
        client = kwargs.get("client")
        result = client.admin.command("getCmdLineOpts")
        self._logger.info("Testing security information...")

        # Check for security settings
        security_settings = result.get("parsed", {}).get("security", {})
        authorization = security_settings.get("authorization", None)
        if authorization != "enabled":
            self.append_item_result(
                "cluster",
                SEVERITY.HIGH,
                "Authorization Disabled",
                "Authorization is disabled, which may lead to unauthorized access."
            )

        redact_logs = security_settings.get("redactClientLogData", None)
        if redact_logs != True:
            self.append_item_result(
                "cluster",
                SEVERITY.MEDIUM,
                "Log Redaction Disabled",
                "Redaction of log is disabled, which may lead to sensitive information exposure."
            )

        net = result.get("parsed", {}).get("net", {})
        tls_enabled = net.get("tls", {}).get("mode", None)
        if tls_enabled is None:
            self.append_item_result(
                "cluster",
                SEVERITY.HIGH,
                "TLS Disabled",
                "TLS is disabled, which may lead to unencrypted connections."
            )
        elif tls_enabled != "requireTLS":
            self.append_item_result(
                "cluster",
                SEVERITY.MEDIUM,
                "Optional TLS",
                f"TLS is enabled but not set to `requireTLS`, current mode is `{tls_enabled}`."
            )

        # TODO: check each node.
        port = net.get("port", None)
        if port == 27017:
            self.append_item_result(
                "cluster",
                SEVERITY.LOW,
                "Default Port Used",
                "Default port `27017` is used, which may expose the server to unnecessary risks."
            )

        self.captured_sample = result