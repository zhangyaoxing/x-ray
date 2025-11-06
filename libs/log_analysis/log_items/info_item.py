from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import *
from libs.utils import *


class InfoItem(BaseItem):
    def __init__(self, output_folder, config):
        super().__init__(output_folder, config)
        self.name = "Basic Info"
        self.description = "Basic information about the instance."
        self._cache = {}
        self._show_scaler = False

        self._ids = [
            20721,  # Process Details
            20722,  # Node is a member of a replica set
            5853300,  # current featureCompatibilityVersion value
            23403,  # Build Info
            51765,  # Operating System
            21951,  # Options set by command line
            4913010,  # Certificate information
            4615611,  # MongoDB starting
        ]

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        index = self._ids.index(log_id) if log_id in self._ids else -1
        attr = log_line.get("attr", {})
        if index == 0 or index == 7:
            # Process Details
            self._process_details(attr)
        elif index == 1:
            # Node is a member of a replica set
            self._process_replica_set(attr)
        elif index == 2:
            # current featureCompatibilityVersion value
            self._process_feature_compatibility(attr)
        elif index == 3:
            # Build Info
            self._process_build_info(attr)
        elif index == 4:
            # Operating System
            self._process_operating_system(attr)
        elif index == 5:
            # Options set by command line
            self._process_command_line_options(attr)
        elif index == 6:
            # Certificate information
            self._process_certificate_info(attr)

    def _process_details(self, attr):
        self._cache["process"] = {
            "pid": attr.get("pid", "Unknown"),
            "host": attr.get("host", "Unknown"),
            "port": attr.get("port", "Unknown"),
        }

    def _process_replica_set(self, attr):
        self._cache["replica_set"] = attr

    def _process_feature_compatibility(self, attr):
        self._cache["fcv"] = attr.get("featureCompatibilityVersion", "Unknown")

    def _process_build_info(self, attr):
        build_info = attr.get("buildInfo", {})
        self._cache["build_info"] = {
            "version": build_info.get("version", "Unknown"),
            "modules": build_info.get("modules", []),
            "environment": build_info.get("environment", {}),
        }

    def _process_operating_system(self, attr):
        os_info = attr.get("os", {})
        self._cache["os"] = {"name": os_info.get("name", "Unknown"), "version": os_info.get("version", "Unknown")}

    def _process_command_line_options(self, attr):
        options = attr.get("options", {})
        self._cache["command_line_options"] = options

    def _process_certificate_info(self, attr):
        cert_info = attr
        self._cache["cert_info"] = cert_info

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        if self._cache == {}:
            f.write("No basic info found in the logs.\n")
            return
        process = self._cache.get("process", None)
        build_info = self._cache.get("build_info", None)
        fcv = self._cache.get("fcv", None)
        if build_info:
            f.write("### Process Info\n\n")
            version = build_info.get("version", "Unknown")
            if "enterprise" in build_info.get("modules", []):
                version += "-ent"
            f.write(f"- MongoDB `{version}` ")
            if fcv:
                f.write(f" (FCV: `{fcv}`)")
            if process:
                f.write(
                    f" PID `{process.get('pid', 'Unknown')}` running on `{process.get('host', 'Unknown')}:{process.get('port', 'Unknown')}`\n"
                )
            f.write("\n")
        cert_info = self._cache.get("cert_info", None)
        if cert_info:
            f.write("### Certificate Info\n\n")
            key_file = cert_info.get("keyFile", "Unknown")
            subject = cert_info.get("subject", "Unknown")
            issuer = cert_info.get("issuer", "Unknown")
            valid_from = cert_info.get("notValidBefore", "Unknown")
            valid_to = cert_info.get("notValidAfter", "Unknown")
            type = cert_info.get("type", "Unknown")
            f.write(f"- Key File: `{key_file}`\n")
            f.write(f"- Type: `{type}`\n")
            f.write(f"- Subject: `{subject}`\n")
            f.write(f"- Issuer: `{issuer}`\n")
            f.write(f"- Valid: `{valid_from}` ~ `{valid_to}`\n\n")
        os = self._cache.get("os", None)
        if os:
            f.write("### Operating System\n\n")
            f.write(f"- {os.get('name', 'Unknown')}\n")
            f.write(f"- {os.get('version', 'Unknown')}\n\n")
        replica_set = self._cache.get("replica_set", {})
        rs_config = replica_set.get("config", None)
        if replica_set:
            f.write("### Replica Set Config\n\n")
            f.write(
                f"Replica Set Name: `{rs_config.get('_id', 'Unknown')}`, member state: `{replica_set.get('memberState', 'Unknown')}`\n\n"
            )
            f.write("|Member|Host|Arbiter|Priority|Votes|Hidden|Delay|\n")
            f.write("|------|----|-------|--------|-----|------|-----|\n")
            for member in rs_config.get("members", []):
                f.write(
                    f"|{member.get('_id', 'Unknown')}|{member.get('host', 'Unknown')}|{member.get('arbiterOnly', False)}|{member.get('priority', 0)}|{member.get('votes', 0)}|{member.get('hidden', False)}|{member.get('secondaryDelaySecs', 0)}|\n"
                )
            f.write("\n")
        command_line_options = self._cache.get("command_line_options", None)
        if command_line_options:
            f.write("### Command Line Options\n\n")
            f.write('<div id="cmd_options">\n')
            f.write("```json\n")
            f.write(to_json(command_line_options, indent=4))
            f.write("\n```\n\n")
            f.write("</div>\n")
