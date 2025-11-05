from libs.log_analysis.log_items.base_item import BaseItem
from bson import json_util
from libs.log_analysis.query_analyzer import analyze_query_pattern
from libs.log_analysis.shared import json_hash, to_json
from libs.utils import escape_markdown, format_json_md

class TopSlowItem(BaseItem):
    """
    Identify the top N slowest operations from the log entries.
    """
    def __init__(self, output_folder: str, config):
        super(TopSlowItem, self).__init__(output_folder, config)
        self._top_n = config.get("top", 10)
        self.name = "Top Slow Operations"
        self.description = f"Identify the top `{self._top_n}` slowest operations from the log entries."
        self._show_scaler = False
        self._cache = {}

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id != 51803:  # Slow query
            return
        attr = log_line.get("attr", {})
        ns = attr.get("ns", "")
        # Skip system namespaces
        if ns.startswith("admin.") or ns.startswith("local.") or ns.startswith("config."):
            return
        duration = attr.get("durationMillis", 0)
        has_sort = attr.get("hasSortStage", False)
        query_hash = attr.get("queryHash", "")
        n_returned = attr.get("nreturned", 0)
        keys_examined = attr.get("keysExamined", 0)
        docs_examined = attr.get("docsExamined", 0)
        plan_summary = attr.get("planSummary", "")
        query_pattern = analyze_query_pattern(log_line)
        if query_hash == "":
            # Some command doesn't have queryHash, e.g., getMore
            # If so, we generate one based on the query shape and sort
            query_hash = json_hash(query_pattern if query_pattern else {}, 4)
            # query_hash = query_pattern.get("hash", "N/A") if query_pattern else "N/A"
        slow_query = self._cache.get(query_hash, None)
        if slow_query is None:
            slow_query = {}
            self._cache[query_hash] = slow_query
        slow_query.update({
            "query_hash": query_hash,
            "ns": ns,
            "query_pattern": query_pattern,
            "duration": slow_query.get("duration", 0) + duration,
            "n_returned": slow_query.get("n_returned", 0) + n_returned,
            "keys_examined": slow_query.get("keys_examined", 0) + keys_examined,
            "docs_examined": slow_query.get("docs_examined", 0) + docs_examined,
            "plan_summary": plan_summary if "plan_summary" not in slow_query else slow_query["plan_summary"],
            "has_sort": has_sort or slow_query.get("has_sort", False),
            "count": slow_query.get("count", 0) + 1,
            "sample": log_line if "sample" not in slow_query else slow_query["sample"],
        })

    def finalize_analysis(self):
        self._cache = list(sorted(self._cache.values(), key=lambda item: item["count"], reverse=True)[:self._top_n])
        # self._cache = list(sorted(self._cache.values(), key=lambda item: item["duration"], reverse=True)[:self._top_n])
        super().finalize_analysis()

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write("<div id=\"top_slow_positioner\"></div>\n\n")
        f.write(f"|Query Hash|Op|Pattern|Details|Plan Summary|\n")
        f.write(f"|---|---|---|---|---|\n")
        # Total Duration (ms)|Count|Avg Duration (ms)|Scanned / Returned|ScannedObj / Returned|Has Sort
        i = 0
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                query_hash = line_json.get("query_hash", "N/A")
                ns = line_json.get("ns", "N/A")
                query_pattern = line_json.get("query_pattern", {})
                op = query_pattern.get("type", "UNKNOWN")
                pattern = query_pattern.get("pattern", {})
                # query_hash = query_hash if query_hash != "" else "N/A"
                duration = line_json.get("duration", 0)
                count = line_json.get("count", 0)
                avg_duration = round(duration / count, 2) if count > 0 else 0
                n_returned = line_json.get("n_returned", 0)
                keys_examined = line_json.get("keys_examined", 0)
                docs_examined = line_json.get("docs_examined", 0)
                has_sort = "Yes" if line_json.get("has_sort", False) else "No"
                scanned_per_returned = round(keys_examined / n_returned, 2) if n_returned > 0 else keys_examined
                scannedobj_per_returned = round(docs_examined / n_returned, 2) if n_returned > 0 else docs_examined
                details = {
                    "Total Duration (ms)": duration,
                    "Count": count,
                    "Avg Duration (ms)": avg_duration,
                    "Targeting": scanned_per_returned,
                    "Targeting (Obj)": scannedobj_per_returned,
                    "Has Sort": has_sort,
                }
                plan_summary = line_json.get("plan_summary", "N/A")
                plan_summary = escape_markdown(plan_summary if plan_summary != "" else "N/A")
                cols = [
                    f"[{query_hash}](#{i})", 
                    f"`{op}` on `{ns}`", 
                    f"<pre>{format_json_md(pattern)}</pre>", 
                    f"<pre>{format_json_md(details)}</pre>", 
                    f"{plan_summary}"
                ]
                f.write(f"|{'|'.join(cols)}|\n")
                i += 1
        f.write("\n```json\n")
        f.write("// Click query hash to display sample query...\n")
        f.write("```\n")