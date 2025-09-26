DATA_TYPES = ["$binary", "$date", "$numberLong", "$numberInt", "$numberDecimal", "$oid", "$timestamp"]
QUERY_OPERATORS = ["$all", "$size", "$elemMatch", # Array operators
                    "$bitsAllClear", "$bitsAllSet", "$bitsAnyClear", "$bitsAnySet", # Bitwise operators
                    "$gt", "$gte", "$lt", "$lte", "$eq", "$ne", "$in", "$nin", # Comparison operators
                    "$exists", "$type", # Data Type operators
                    "$box", "$center", "$centerSphere", "$geoIntersects", "$geometry", "$geoWithin", 
                    "$maxDistance", "$minDistance", "$near", "$nearSphere", "$polygon", # Geospatial operators
                    "$and", "$or", "$not", "$nor", # Logical operators
                    "$expr", "$jsonSchema", "$mod", "$regex", "$where", # Other operators
                    "$text", "$comment"] # Text search operators
SIMPLE_OPERATORS = ["$gt", "$gte", "$lt", "$lte", "$eq", "$ne", "$in", "$nin", "$exists", "$type", "$mod", 
                    "$regex", "$size", "$all", "$bitsAllClear", "$bitsAllSet", "$bitsAnyClear", "$bitsAnySet", 
                    "$box", "$center", "$centerSphere", "$geoIntersects", "$geometry", "$geoWithin", 
                    "$maxDistance", "$minDistance", "$near", "$nearSphere", "$polygon", "$text", "$comment"]
COMPLEX_OPERATORS = ["$elemMatch", "$and", "$or", "$not", "$nor", "$expr", "$jsonSchema"]

def analyze_query_pattern(log_line):
    query_type = "command"
    query = {}
    msg = log_line.get("msg", "")
    if msg != "Slow query":
        return None
    attr = log_line.get("attr", {})
    type = attr.get("type", "")
    command = attr.get("command", {})
    if type == "update":
        # The real update command
        query_type = "update"
        query = command.get("q", {})
    elif "update" in command:
        # The update command can contain multiple updates
        query_type = "update.$cmd"
        query = command.get("updates", [])
        # if isinstance(query, list) and len(query) > 0:
        #     query = query[0].get("q", {})
    elif "aggregate" in command:
        query_type = "aggregate"
        query = command.get("pipeline", [])
        # This is not correct, but should cover 90% of cases
        # We only handle simple $match stage for now
        first_stage = query[0] if len(query) > 0 else {}
        if "$match" in first_stage:
            query = first_stage["$match"]
    elif "find" in command:
        query_type = "find"
        query = command.get("filter", {})
    elif "getMore" in command:
        query_type = "getmore"
        query = attr.get("originatingCommand", {}).get("filter", {})
    elif "insert" in command:
        query_type = "insert"
        query = {}
    elif "delete" in command:
        query_type = "remove.$cmd"
        query = command.get("deletes", [])
        # if isinstance(query, list) and len(query) > 0:
        #     query = query[0].get("q", {})
    elif type == "remove":
        query_type = "remove"
        query = command.get("q", {})
    elif "findAndModify" in command:
        query_type = "findandmodify"
        query = command.get("query", {})

    if isinstance(query, list):
        # For list of queries, e.g., update.$cmd, remove.$cmd
        patterns = []
        for q in query:
            q_pattern = query_to_pattern(q.get("q", {}))
            patterns.append(q_pattern)
        return query_type, patterns
    else:
        # For single query
        return query_type, query_to_pattern(query)

def query_to_pattern(query):
    shape = {}
    if isinstance(query, list):
        shape = [ query_to_pattern(i) for i in query ]
        # If all elements are 1, simplify to 1
        if all(i == 1 for i in shape):
            shape = 1
    elif isinstance(query, dict):
        for k, v in query.items():
            if k in COMPLEX_OPERATORS:
                shape[k] = query_to_pattern(v)
            else:
                shape[k] = _query_to_pattern(v)
    return shape

def _query_to_pattern(query):
    shape = {}
    if isinstance(query, list):
        shape = [ _query_to_pattern(i) for i in query ]
        # If all elements are 1, simplify to 1
        if all(i == 1 for i in shape):
            shape = 1
    elif isinstance(query, dict):
        for k, v in query.items():
            if k in COMPLEX_OPERATORS:
                shape[k] = query_to_pattern(v)
            elif k in SIMPLE_OPERATORS:
                shape[k] = 1
            else:
                shape = 1
    else:
        shape = 1
    return shape
    