from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash
from bson import json_util
from libs.utils import *
from re import search, split

COMPATIBILITY_MATRIX_JSON = "compatibility_matrix.json"

class ClientMetaItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(ClientMetaItem, self).__init__(output_folder, config)
        self._cache = {}
        self.name = "Client Metadata"
        self.description = "Visualize client metadata."
        self._cache = {}
        self._show_scaler = False

    def analyze(self, log_line):
        super().analyze(log_line)
        log_id = log_line.get("id", "")
        if log_id != 51800: # Client metadata
            return
        attr = log_line.get("attr", {})
        ip = attr["remote"].split(":")[0]
        doc = attr["doc"]
        doc_hash = json_hash(doc)
        if doc_hash not in self._cache:
            self._cache[doc_hash] = {
                "doc": doc
            }
        if "ips" not in self._cache[doc_hash]:
            self._cache[doc_hash]["ips"] = {}
        self._cache[doc_hash]["ips"][ip] = self._cache[doc_hash]["ips"].get(ip, 0) + 1

    def finalize_analysis(self):
        cache = []
        for v in self._cache.values():
            doc = v["doc"]
            ips = [{"ip": ip, "count": count} for ip, count in v.get("ips", {}).items()]
            cache.append({
                "doc": doc,
                "ips": ips
            })
        self._cache = cache
        super().finalize_analysis()
        # Based on the server version, find out minimum compatible driver versions.
        with open(COMPATIBILITY_MATRIX_JSON, "r") as f:
            compatibility_matrix = json.load(f)
        server_compatible_version = self._server_version.to_compatibility_str() if self._server_version else "Unknown"
        driver_matrix = compatibility_matrix.get(server_compatible_version, {})
        self._driver_matrix = {k: Version(v) for k, v in driver_matrix.items()}

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f"|Application|Driver|OS|Platform|Client IPs|\n")
        f.write(f"|---|---|---|---|---|\n")
        rows = []
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                doc = line_json.get("doc", {})
                full_app = doc.get("application", {}).get("name", "Unknown")
                trunc_app = truncate_content(full_app)
                app_html = tooltip_html(escape_markdown(full_app), escape_markdown(trunc_app)) if full_app != trunc_app else escape_markdown(full_app)
                driver = doc.get("driver", {})
                driver_name = driver.get("name", "Unknown")
                driver_version = driver.get("version", "Unknown")
                full_driver = escape_markdown(f"{driver_name} {driver_version}")
                is_compatible = is_driver_compatible(driver_name, driver_version, self._server_version, self._driver_matrix)
                if not is_compatible:
                    full_driver = f"<span style=\"color:red;\">{full_driver}</span>"
                os = doc.get("os", {})
                os_type = os.get("type", "Unknown")
                os_name = os.get("name", "Unknown")
                os_arch = os.get("architecture", "Unknown")
                os_version = os.get("version", "Unknown")
                os_str = escape_markdown(f"{os_name if os_name != 'Unknown' else os_type} {os_arch} {os_version if os_version != 'Unknown' else ''}")
                platform = escape_markdown(doc.get("platform", "Unknown"))
                ips = [f"{ip['ip']} ({ip['count']} times)" for ip in line_json["ips"]]
                ips_html = tooltip_html(", ".join(ips), f"{ips[0]} {'...' if len(ips) > 1 else ''}")
                rows.append([app_html, full_driver, os_str, platform, ips_html])
        # Sort by Application name, then driver name
        sorted_rows = sorted(rows, key=lambda x: (x[0].lower(), x[1].lower()))
        for row in sorted_rows:
            f.write("|".join(row) + "\n")
        if self._server_version:
            f.write(f"\n**Drivers that doesn't support current MongoDB <span style=\"color: red;\">{self._server_version}</span> are marked <span style=\"color:red;\">RED</span>.**\n")
        else:
            f.write(f"\n**<span style=\"color: red;\">Unable to determine server version to mark incompatible drivers. Log may be truncated by user.</span>**\n")
        f.write(f"<div class=\"pie\"><canvas id='canvas_{self.__class__.__name__}'></canvas></div>\n")
        f.write(f"<div class=\"pie\"><canvas id='canvas_{self.__class__.__name__}_ip'></canvas></div>\n")
    
def is_driver_compatible(log_driver_name: str, log_driver_version: str, server_version: Version, matrix) -> bool:
    if not server_version or log_driver_version == "Unknown":
        # If can't determine server version, assume compatible.
        # But log a warning and display a message on the report.
        logger.warning(yellow(f"Cannot determine compatibility for driver version: {log_driver_name} {log_driver_version}"))
        return True
    try:
        # Check which driver name appeared in the log_driver_name. That's the driver we need.
        driver_name = None
        min_version = None
        for k, v in matrix.items():
            if k in log_driver_name:
                # Some drivers uses other drivers internally
                # E.g. PHP uses the C driver, Scala uses the Java driver
                # The sequence matters here, so we take the last match
                driver_name = k
                min_version = v

        driver_ver = parse_version_from_log(log_driver_name, log_driver_version, driver_name)
        return not driver_ver or driver_ver >= min_version
    except Exception as e:
        logger.warning(f"Failed to parse driver version: {log_driver_version}, error: {e}")
        return True
        
def parse_version_from_log(driver_name: str, driver_version: str, target_driver_name: str) -> Version:
    """Parse driver version from log line"""
    # Driver version from the log can have different forms. Some examples are:
    #  - {"name":"mongo-csharp-driver","version":"2.21.0.0"}
    #  - {"name":"mongo-java-driver|sync","version":"3.12.10"}
    #  - {"name":"mongoc / mongocxx","version":"1.26.3 / 3.8.1"}
    #  - {"name":"mongoc / ext-mongodb:PHP / PHPLIB/symfony-mongodb ","version":"1.25.2 / 1.17.2 / 1.17.0/2.6.1 "}
    #  - {"name":"mongo-java-driver|mongo-scala-driver","version":"unknown|2.3.0"}
    #  - {"name":"mongo-go-driver","version":"v1.12.0-cloud"}
    # We need to extract the relevant part for comparison.
    # Some drivers are internal only, e.g., NetworkInterfaceTL, we skip those.
    #  - {"name":"NetworkInterfaceTL","version":"5.0.31"}
    name_parts = [part.strip(" ") for part in split("[|/]", driver_name)]
    version_parts = [part.strip(" ") for part in split("[|/]", driver_version)]
    for name_part, version_part in zip(name_parts, version_parts):
        if name_part == target_driver_name:
            version = search(r'\d+(\.\d+)*', version_part.strip())
            return Version.parse(version.group(0) if version else None)
    # Because | is used both as delimiter and in driver names, we need to do one more check
    # Drivers like mongo-java-driver|sync will go here if not matched above
    if target_driver_name == driver_name:
        version = search(r'\d+(\.\d+)*', driver_version.strip())
        return Version.parse(version.group(0) if version else None)