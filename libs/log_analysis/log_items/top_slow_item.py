from libs.log_analysis.log_items.base_item import BaseItem
from bson import json_util
from libs.log_analysis.shared import escape_markdown

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
        msg = log_line.get("msg", "")
        if msg != "Slow query":
            return
        attr = log_line.get("attr", {})
        duration = attr.get("durationMillis", 0)
        has_sort = attr.get("hasSortStage", False)
        query_hash = attr.get("queryHash", "")
        n_returned = attr.get("nreturned", 0)
        keys_examined = attr.get("keysExamined", 0)
        docs_examined = attr.get("docsExamined", 0)
        plan_summary = attr.get("planSummary", "")
        slow_query = self._cache.get(query_hash, None)
        if slow_query is None:
            slow_query = {}
            self._cache[query_hash] = slow_query
        slow_query.update({
            "query_hash": query_hash,
            "duration": slow_query.get("duration", 0) + duration,
            "n_returned": slow_query.get("n_returned", 0) + n_returned,
            "keys_examined": slow_query.get("keys_examined", 0) + keys_examined,
            "docs_examined": slow_query.get("docs_examined", 0) + docs_examined,
            "plan_summary": plan_summary if "plan_summary" not in slow_query else slow_query["plan_summary"],
            "has_sort": has_sort or slow_query.get("has_sort", False),
            "count": slow_query.get("count", 0) + 1,
            "sample": log_line if "sample" not in slow_query else slow_query["sample"],
        })
    def finalize(self):
        self._cache = list(sorted(self._cache.values(), key=lambda item: item["duration"], reverse=True)[:self._top_n])
        super().finalize()
    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write("<div id=\"top_slow_positioner\"></div>\n\n")
        f.write(f"|Query Hash|Total Duration (ms)|Count|Avg Duration (ms)|Scanned/Returned|ScannedObj/Returned|Has Sort|Plan Summary|\n")
        f.write(f"|---|---|---|---|---|---|---|---|\n")
        i = 0
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                query_hash = line_json.get("query_hash", "N/A")
                query_hash = query_hash if query_hash != "" else "N/A"
                duration = line_json.get("duration", 0)
                count = line_json.get("count", 0)
                avg_duration = round(duration / count, 2) if count > 0 else 0
                n_returned = line_json.get("n_returned", 0)
                keys_examined = line_json.get("keys_examined", 0)
                docs_examined = line_json.get("docs_examined", 0)
                has_sort = "Yes" if line_json.get("has_sort", False) else "No"
                plan_summary = line_json.get("plan_summary", "N/A")
                plan_summary = escape_markdown(plan_summary if plan_summary != "" else "N/A")
                scanned_per_returned = round(keys_examined / n_returned, 2) if n_returned > 0 else keys_examined
                scannedobj_per_returned = round(docs_examined / n_returned, 2) if n_returned > 0 else docs_examined
                f.write(f"|[{query_hash}](#{i})|{duration}|{count}|{avg_duration}|{scanned_per_returned}|{scannedobj_per_returned}|{has_sort}|{plan_summary}|\n")
                i += 1
        f.write("\n```json\n")
        f.write("// Click query hash to display sample slow query...\n")
        f.write("```\n")