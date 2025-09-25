def analyze_query_shape(log_line):
    msg = log_line.get("msg", "")
    if msg != "Slow query":
        return None
    attr = log_line.get("attr", {})
    type = attr.get("type", "")
    ns = attr.get("ns", "")
    command = attr.get("command", {})
    if type == "update":
        query = command.get("q", {})
    elif "aggregate" in command:
        query = command.get("pipeline", [])
    elif "find" in command:
        query = command.get("filter", {})
    elif "getMore" in command:
        query = attr.get("originatingCommand", {}).get("filter", {})
    else:
        query = {}
    return query_to_shape(query)

def query_to_shape(query):
    shape = {}
    if isinstance(query, list):
        # For aggregation pipelines
        # Only check the 1st stage. It's not fully correct but should cover 90% of cases.
        stage1 = query[0] if len(query) > 0 else {}
        if "$match" in stage1:
            return query_to_shape(stage1["$match"])
        else:
            return {}
    else:
        for k, v in query.items():
            if isinstance(v, dict):
                shape[k] = query_to_shape(v)
            elif isinstance(v, list):
                shape[k] = [query_to_shape(i) if isinstance(i, dict) else 1 for i in v]
                # If all elements are 1, simplify to []
                if all(i == 1 for i in shape[k]):
                    shape[k] = 1
            else:
                shape[k] = 1
    return shape
    