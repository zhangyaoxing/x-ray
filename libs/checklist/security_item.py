from pymongo import MongoClient
from libs.checklist.base_item import BaseItem, SEVERITY, CATEGORY
from libs.utils import *

class SecurityItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Security"
        self._description = "Collects & review security related information."
        self._category = CATEGORY.SECURITY

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering security information...")
        client = MongoClient(kwargs.get("client"))
        result = client.admin.command("getCmdLineOpts")
        self._logger.info("Testing security information...")

        # Check for security settings
        security_settings = result.get("parsed", {}).get("security", {})
        authorization = security_settings.get("authorization", None)
        if authorization != "enabled":
            self._test_result.append({
                "severity": SEVERITY.HIGH,
                "message": "Authorization is not enabled, which may lead to unauthorized access."
            })

        redact_logs = security_settings.get("redactClientLogData", None)
        if redact_logs != True:
            self._test_result.append({
                "severity": SEVERITY.MEDIUM,
                "message": "Redaction of client log data is not enabled, which may lead to sensitive information exposure."
            })
        
        net = result.get("parsed", {}).get("net", {})
        tls_enabled = net.get("tls", {}).get("mode", None)
        if tls_enabled is None:
            self._test_result.append({
                "severity": SEVERITY.HIGH,
                "message": "TLS is not enabled, which may lead to unencrypted connections."
            })
        elif tls_enabled != "requireTLS":
            self._test_result.append({
                "severity": SEVERITY.MEDIUM,
                "message": f"TLS is enabled but not set to `requireTLS`, current mode is `{tls_enabled}`."
            })

        port = net.get("port", None)
        if port == 27017:
            self._test_result.append({
                "severity": SEVERITY.MEDIUM,
                "message": "Default port `27017` is used, which may expose the server to unnecessary risks."
            })

        self.sample_result = result