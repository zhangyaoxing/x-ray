from bson import json_util
from libs.log_analysis.query_analyzer import analyze_query_pattern, query_to_pattern

slow_insert = json_util.loads('{"t": {"$date": "2025-09-24T13:14:17.239Z"}, "s": "I", "c": "COMMAND", "id": 51803, "ctx": "monitoring-keys-for-HMAC", "msg": "Slow query", "attr": {"type": "command", "ns": "admin.system.keys", "command": {"insert": "system.keys", "bypassDocumentValidation": false, "ordered": true, "documents": [{"purpose": "HMAC", "key": {"$binary": {"base64": "BV7WzBYMtJ+FoTcRK8LryAmIuBk=", "subType": "00"}}, "expiresAt": {"$timestamp": {"t": 1766495656, "i": 0}}, "_id": 7553643405352370178}], "writeConcern": {"w": "majority", "wtimeout": 60000}, "$db": "admin"}, "ninserted": 1, "keysInserted": 1, "numYields": 0, "reslen": 230, "locks": {"ParallelBatchWriterMode": {"acquireCount": {"r": 1}}, "FeatureCompatibilityVersion": {"acquireCount": {"r": 1, "w": 1}}, "ReplicationStateTransition": {"acquireCount": {"w": 1}, "acquireWaitCount": {"w": 1}, "timeAcquiringMicros": {"w": 1401}}, "Global": {"acquireCount": {"r": 1, "w": 1}}, "Database": {"acquireCount": {"w": 1}}, "Collection": {"acquireCount": {"w": 1}}, "Mutex": {"acquireCount": {"r": 2}}}, "flowControl": {"acquireCount": 1, "timeAcquiringMicros": 2}, "writeConcern": {"w": "majority", "wtimeout": 60000, "provenance": "clientSupplied"}, "storage": {"data": {"bytesRead": 473, "timeReadingMicros": 9}}, "protocol": "op_msg", "durationMillis": 778}}')
slow_find = json_util.loads('{"t": {"$date": "2025-09-24T13:21:32.148Z"}, "s": "I", "c": "COMMAND", "id": 51803, "ctx": "conn40", "msg": "Slow query", "attr": {"type": "command", "ns": "test.pizzas", "appName": "mongosh 2.5.6", "command": {"find": "pizzas", "filter": {"size": "medium"}, "lsid": {"id": {"$binary": {"base64": "H4tLG7+9SPiyukZ8sfmfXg==", "subType": "04"}}}, "$clusterTime": {"clusterTime": {"$timestamp": {"t": 1758720086, "i": 1}}, "signature": {"hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}}, "keyId": 0}}, "$readPreference": {"mode": "primaryPreferred"}, "$db": "test"}, "planSummary": "COLLSCAN", "keysExamined": 0, "docsExamined": 7, "cursorExhausted": true, "numYields": 0, "nreturned": 3, "queryHash": "F1FEE1FA", "planCacheKey": "5ADDE2B9", "reslen": 412, "locks": {"FeatureCompatibilityVersion": {"acquireCount": {"r": 1}}, "Global": {"acquireCount": {"r": 1}}, "Mutex": {"acquireCount": {"r": 1}}}, "readConcern": {"level": "local", "provenance": "implicitDefault"}, "storage": {}, "remote": "127.0.0.1:56678", "protocol": "op_msg", "durationMillis": 0}}')
slow_aggregate = json_util.loads('{"t": {"$date": "2025-09-24T13:21:28.063Z"}, "s": "I", "c": "COMMAND", "id": 51803, "ctx": "conn40", "msg": "Slow query", "attr": {"type": "command", "ns": "test.pizzas", "appName": "mongosh 2.5.6", "command": {"aggregate": "pizzas", "pipeline": [{"$match": {"size": {"$in": ["small", "medium", "large"]}}}, {"$group": {"_id": "$size", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}], "cursor": {}, "lsid": {"id": {"$binary": {"base64": "H4tLG7+9SPiyukZ8sfmfXg==", "subType": "04"}}}, "$clusterTime": {"clusterTime": {"$timestamp": {"t": 1758720076, "i": 1}}, "signature": {"hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}}, "keyId": 0}}, "$readPreference": {"mode": "primaryPreferred"}, "$db": "test"}, "planSummary": "COLLSCAN", "keysExamined": 0, "docsExamined": 7, "hasSortStage": true, "cursorExhausted": true, "numYields": 0, "nreturned": 3, "queryHash": "BA2D5E3A", "planCacheKey": "69EA54FF", "reslen": 328, "locks": {"FeatureCompatibilityVersion": {"acquireCount": {"r": 2}}, "Global": {"acquireCount": {"r": 2}}, "Mutex": {"acquireCount": {"r": 2}}}, "readConcern": {"level": "local", "provenance": "implicitDefault"}, "writeConcern": {"w": "majority", "wtimeout": 0, "provenance": "implicitDefault"}, "storage": {}, "remote": "127.0.0.1:56678", "protocol": "op_msg", "durationMillis": 0}}')
slow_cmd = json_util.loads('{"t":{"$date":"2025-09-24T16:46:17.078+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn53","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"createIndexes":"pizzas","indexes":[{"name":"type_1","key":{"type":1}}],"lsid":{"id":{"$uuid":"ee544a5a-d47b-4ee5-9ca1-f2859e69a650"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758725176,"i":7}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"numYields":0,"reslen":271,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":3}},"FeatureCompatibilityVersion":{"acquireCount":{"r":3,"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":5}},"Global":{"acquireCount":{"r":3,"w":2}},"Database":{"acquireCount":{"r":2,"w":1}},"Collection":{"acquireCount":{"r":2,"W":1}},"Mutex":{"acquireCount":{"r":3}}},"flowControl":{"acquireCount":2,"timeAcquiringMicros":2},"readConcern":{"level":"local","provenance":"implicitDefault"},"writeConcern":{"w":"majority","wtimeout":0,"provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:49701","protocol":"op_msg","durationMillis":213}}')
slow_getmore = json_util.loads('{"t":{"$date":"2025-09-24T16:46:17.089+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn53","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"getMore":2225429849964214763,"collection":"pizzas","batchSize":1,"lsid":{"id":{"$uuid":"ee544a5a-d47b-4ee5-9ca1-f2859e69a650"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758725177,"i":2}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"originatingCommand":{"find":"pizzas","filter":{"size":{"$in":["small","medium","large"]}},"batchSize":1,"lsid":{"id":{"$uuid":"ee544a5a-d47b-4ee5-9ca1-f2859e69a650"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758725177,"i":2}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"planSummary":"COLLSCAN","cursorid":2225429849964214763,"keysExamined":0,"docsExamined":1,"numYields":0,"nreturned":1,"reslen":292,"locks":{"FeatureCompatibilityVersion":{"acquireCount":{"r":1}},"Global":{"acquireCount":{"r":1}},"Mutex":{"acquireCount":{"r":1}}},"readConcern":{"level":"local","provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:49701","protocol":"op_msg","durationMillis":0}}')
slow_delete_cmd = json_util.loads('{"t":{"$date":"2025-09-25T23:41:05.378+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn26","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.$cmd","appName":"mongosh 2.5.6","command":{"delete":"pizzas","deletes":[{"q":{"type":"pineapple"},"limit":1}],"ordered":true,"lsid":{"id":{"$uuid":"eef6660c-6ef9-4492-a285-fab357f0b335"}},"txnNumber":2,"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758836465,"i":14}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"numYields":0,"reslen":230,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":2}},"FeatureCompatibilityVersion":{"acquireCount":{"r":1,"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":4}},"Global":{"acquireCount":{"r":1,"w":2}},"Database":{"acquireCount":{"w":2}},"Collection":{"acquireCount":{"w":2}},"Mutex":{"acquireCount":{"r":2}}},"flowControl":{"acquireCount":1,"timeAcquiringMicros":1},"readConcern":{"level":"local","provenance":"implicitDefault"},"writeConcern":{"w":"majority","wtimeout":0,"provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:51204","protocol":"op_msg","durationMillis":15}}')
slow_delete = json_util.loads('{"t":{"$date":"2025-09-25T23:41:05.365+02:00"},"s":"I",  "c":"WRITE",    "id":51803,   "ctx":"conn26","msg":"Slow query","attr":{"type":"remove","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"q":{"type":"pineapple"},"limit":1},"planSummary":"IXSCAN { type: 1 }","keysExamined":1,"docsExamined":1,"ndeleted":1,"keysDeleted":2,"numYields":0,"queryHash":"2A1623C7","planCacheKey":"CDFEBC4E","locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":2}},"FeatureCompatibilityVersion":{"acquireCount":{"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":3}},"Global":{"acquireCount":{"w":2}},"Database":{"acquireCount":{"w":2}},"Collection":{"acquireCount":{"w":2}},"Mutex":{"acquireCount":{"r":2}}},"flowControl":{"acquireCount":1,"timeAcquiringMicros":1},"readConcern":{"level":"local","provenance":"implicitDefault"},"storage":{"data":{"bytesRead":152,"timeReadingMicros":2}},"remote":"127.0.0.1:51204","durationMillis":2}}')
slow_update = json_util.loads('{"t":{"$date":"2025-09-25T23:56:25.137+02:00"},"s":"I",  "c":"WRITE",    "id":51803,   "ctx":"conn28","msg":"Slow query","attr":{"type":"update","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"q":{"type":"pineapple"},"u":{"$set":{"price":{"$inc":-1}}},"multi":false,"upsert":false},"planSummary":"IXSCAN { type: 1 }","keysExamined":1,"docsExamined":1,"nMatched":1,"nModified":1,"nUpserted":0,"numYields":0,"queryHash":"2A1623C7","planCacheKey":"CDFEBC4E","locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":2}},"FeatureCompatibilityVersion":{"acquireCount":{"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":3}},"Global":{"acquireCount":{"w":2}},"Database":{"acquireCount":{"w":2}},"Collection":{"acquireCount":{"w":2}},"Mutex":{"acquireCount":{"r":2}}},"flowControl":{"acquireCount":1,"timeAcquiringMicros":1},"readConcern":{"level":"local","provenance":"implicitDefault"},"storage":{"data":{"bytesRead":152,"timeReadingMicros":1}},"remote":"127.0.0.1:51206","durationMillis":0}}')
slow_update_cmd = json_util.loads('{"t":{"$date":"2025-09-25T23:56:25.149+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn28","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.$cmd","appName":"mongosh 2.5.6","command":{"update":"pizzas","updates":[{"q":{"type":"pineapple"},"u":{"$set":{"price":{"$inc":-1}}}}],"ordered":true,"lsid":{"id":{"$uuid":"9312b172-7afe-4990-ae1d-429f883088c7"}},"txnNumber":2,"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758837385,"i":5}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"numYields":0,"reslen":245,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":2}},"FeatureCompatibilityVersion":{"acquireCount":{"r":1,"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":4}},"Global":{"acquireCount":{"r":1,"w":2}},"Database":{"acquireCount":{"w":2}},"Collection":{"acquireCount":{"w":2}},"Mutex":{"acquireCount":{"r":2}}},"flowControl":{"acquireCount":1,"timeAcquiringMicros":1},"readConcern":{"level":"local","provenance":"implicitDefault"},"writeConcern":{"w":"majority","wtimeout":0,"provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:51206","protocol":"op_msg","durationMillis":13}}')
slow_findandmodify = json_util.loads('{"t":{"$date":"2025-09-26T00:02:01.797+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn27","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"findAndModify":"pizzas","query":{"type":"pineapple"},"remove":false,"new":false,"upsert":false,"update":{"$set":{"price":20}},"lsid":{"id":{"$uuid":"c6525f30-f9d7-4e61-affd-2ce438fecfc8"}},"txnNumber":2,"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758837721,"i":14}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"planSummary":"IXSCAN { type: 1 }","keysExamined":1,"docsExamined":1,"nMatched":1,"nModified":1,"nUpserted":0,"numYields":0,"queryHash":"2A1623C7","planCacheKey":"CDFEBC4E","reslen":278,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":2}},"FeatureCompatibilityVersion":{"acquireCount":{"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":3}},"Global":{"acquireCount":{"w":2}},"Database":{"acquireCount":{"w":2}},"Collection":{"acquireCount":{"w":2}},"Mutex":{"acquireCount":{"r":2}}},"flowControl":{"acquireCount":1,"timeAcquiringMicros":1},"readConcern":{"level":"local","provenance":"implicitDefault"},"writeConcern":{"w":"majority","wtimeout":0,"provenance":"implicitDefault"},"storage":{"data":{"bytesRead":152,"timeReadingMicros":2}},"remote":"127.0.0.1:51205","protocol":"op_msg","durationMillis":13}}')

def test_query_analyzer():
    pattern = analyze_query_pattern(slow_insert)
    assert pattern["pattern"] == {} and pattern["type"] == "insert"
    pattern = analyze_query_pattern(slow_find)
    assert pattern["pattern"] == {"size": 1} and pattern["type"] == "find"
    pattern = analyze_query_pattern(slow_aggregate)
    assert pattern["pattern"] == {"size": {"$in": 1}} and pattern["type"] == "aggregate"
    pattern = analyze_query_pattern(slow_cmd)
    assert pattern["pattern"] == {} and pattern["type"] == "command"
    pattern = analyze_query_pattern(slow_getmore)
    assert pattern["pattern"] == {"size": {"$in": 1}} and pattern["type"] == "getmore"
    pattern = analyze_query_pattern(slow_delete)
    assert pattern["pattern"] == {"type": 1} and pattern["type"] == "remove"
    pattern = analyze_query_pattern(slow_delete_cmd)
    assert pattern["pattern"] == [{"type": 1}] and pattern["type"] == "remove.$cmd"
    pattern = analyze_query_pattern(slow_update)
    assert pattern["pattern"] == {"type": 1} and pattern["type"] == "update"
    pattern = analyze_query_pattern(slow_update_cmd)
    assert pattern["pattern"] == [{"type": 1}] and pattern["type"] == "update.$cmd"


def test_query_to_shape_complex():
    # Complex operators
    query = {
        "items": {
            "$elemMatch": {
                "name": "item1",
                "price": {"$gt": 10}
            }
        }
    }
    pattern = query_to_pattern(query)
    assert pattern == {"items": {"$elemMatch": {"name": 1, "price": {"$gt": 1}}}}

    query = {"$or": [ {"status": "A"}, {"qty": {"$lt": 30}} ]}
    pattern = query_to_pattern(query)
    assert pattern == {"$or": [ {"status": 1}, {"qty": {"$lt": 1}} ]}

    query = {"$and": [ {"age": {"$gt": 25}}, {"$or": [{"age": {"$lt": 50}}, {"location": "USA"}]} ]}
    pattern = query_to_pattern(query)
    assert pattern == {"$and": [ {"age": {"$gt": 1}}, {"$or": [{"age": {"$lt": 1}}, {"location": 1}]} ]}

def test_query_to_shape_simple():
    # Simple operators
    query = {"$text": {"$search": "coffee"}}
    pattern = query_to_pattern(query)
    assert pattern == {"$text": 1}

    query = {
       "location": { 
           "$near": {
               "$geometry": { "type": "Point",  "coordinates": [ -73.9667, 40.78 ] },
                "$minDistance": 1000,
                "$maxDistance": 5000
            }
       }
    }
    pattern = query_to_pattern(query)
    assert pattern == {"location": {"$near": 1}}

    query = {"size": "medium"}
    pattern = query_to_pattern(query)
    assert pattern == {"size": 1}

    query = {"age": {"$gt": 30}, "status": "A"}
    pattern = query_to_pattern(query)
    assert pattern == {"age": {"$gt": 1}, "status": 1}

    query = {"tags": ["red", "blank"]}
    pattern = query_to_pattern(query)
    assert pattern == {"tags": 1}

def test_query_to_shape_no_operator():
    # No operator
    query = {"items": {"sku": 1000}}
    shape = query_to_pattern(query)
    assert shape == {"items": 1}

    query = {"items": [{"name": "item1"}, {"name": "item2"}]}
    shape = query_to_pattern(query)
    assert shape == {"items": 1}

    query = {}
    shape = query_to_pattern(query)
    assert shape == {}