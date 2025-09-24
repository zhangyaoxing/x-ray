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
    return {}
    