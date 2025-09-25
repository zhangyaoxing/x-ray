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
        # This is not correct, but should cover 90% of cases
        # We only handle simple $match stage for now
        first_stage = query[0] if len(query) > 0 else {}
        if "$match" in first_stage:
            query = first_stage["$match"]
        else:
            query = {}
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
        shape = [ query_to_shape(i) for i in query ]
        # If all elements are 1, simplify to 1
        if all(i == 1 for i in shape):
            shape = 1
    elif isinstance(query, dict):
        for k, v in query.items():
            if k in COMPLEX_OPERATORS:
                shape[k] = query_to_shape(v)
            else:
                shape[k] = _query_to_shape(v)
    return shape

def _query_to_shape(query):
    shape = {}
    if isinstance(query, list):
        shape = [ _query_to_shape(i) for i in query ]
        # If all elements are 1, simplify to 1
        if all(i == 1 for i in shape):
            shape = 1
    elif isinstance(query, dict):
        for k, v in query.items():
            if k in COMPLEX_OPERATORS:
                shape[k] = query_to_shape(v)
            elif k in SIMPLE_OPERATORS:
                shape[k] = 1
            else:
                shape = 1
    else:
        shape = 1
    return shape
    