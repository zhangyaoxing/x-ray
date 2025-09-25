from bson import json_util as json_utils
from libs.log_analysis.query_analyzer import analyze_query_shape, query_to_shape

slow_insert = json_utils.loads('{"t": {"$date": "2025-09-24T13:14:17.239Z"}, "s": "I", "c": "COMMAND", "id": 51803, "ctx": "monitoring-keys-for-HMAC", "msg": "Slow query", "attr": {"type": "command", "ns": "admin.system.keys", "command": {"insert": "system.keys", "bypassDocumentValidation": false, "ordered": true, "documents": [{"purpose": "HMAC", "key": {"$binary": {"base64": "BV7WzBYMtJ+FoTcRK8LryAmIuBk=", "subType": "00"}}, "expiresAt": {"$timestamp": {"t": 1766495656, "i": 0}}, "_id": 7553643405352370178}], "writeConcern": {"w": "majority", "wtimeout": 60000}, "$db": "admin"}, "ninserted": 1, "keysInserted": 1, "numYields": 0, "reslen": 230, "locks": {"ParallelBatchWriterMode": {"acquireCount": {"r": 1}}, "FeatureCompatibilityVersion": {"acquireCount": {"r": 1, "w": 1}}, "ReplicationStateTransition": {"acquireCount": {"w": 1}, "acquireWaitCount": {"w": 1}, "timeAcquiringMicros": {"w": 1401}}, "Global": {"acquireCount": {"r": 1, "w": 1}}, "Database": {"acquireCount": {"w": 1}}, "Collection": {"acquireCount": {"w": 1}}, "Mutex": {"acquireCount": {"r": 2}}}, "flowControl": {"acquireCount": 1, "timeAcquiringMicros": 2}, "writeConcern": {"w": "majority", "wtimeout": 60000, "provenance": "clientSupplied"}, "storage": {"data": {"bytesRead": 473, "timeReadingMicros": 9}}, "protocol": "op_msg", "durationMillis": 778}}')
slow_find = json_utils.loads('{"t": {"$date": "2025-09-24T13:21:32.148Z"}, "s": "I", "c": "COMMAND", "id": 51803, "ctx": "conn40", "msg": "Slow query", "attr": {"type": "command", "ns": "test.pizzas", "appName": "mongosh 2.5.6", "command": {"find": "pizzas", "filter": {"size": "medium"}, "lsid": {"id": {"$binary": {"base64": "H4tLG7+9SPiyukZ8sfmfXg==", "subType": "04"}}}, "$clusterTime": {"clusterTime": {"$timestamp": {"t": 1758720086, "i": 1}}, "signature": {"hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}}, "keyId": 0}}, "$readPreference": {"mode": "primaryPreferred"}, "$db": "test"}, "planSummary": "COLLSCAN", "keysExamined": 0, "docsExamined": 7, "cursorExhausted": true, "numYields": 0, "nreturned": 3, "queryHash": "F1FEE1FA", "planCacheKey": "5ADDE2B9", "reslen": 412, "locks": {"FeatureCompatibilityVersion": {"acquireCount": {"r": 1}}, "Global": {"acquireCount": {"r": 1}}, "Mutex": {"acquireCount": {"r": 1}}}, "readConcern": {"level": "local", "provenance": "implicitDefault"}, "storage": {}, "remote": "127.0.0.1:56678", "protocol": "op_msg", "durationMillis": 0}}')
slow_aggregate = json_utils.loads('{"t": {"$date": "2025-09-24T13:21:28.063Z"}, "s": "I", "c": "COMMAND", "id": 51803, "ctx": "conn40", "msg": "Slow query", "attr": {"type": "command", "ns": "test.pizzas", "appName": "mongosh 2.5.6", "command": {"aggregate": "pizzas", "pipeline": [{"$match": {"size": {"$in": ["small", "medium", "large"]}}}, {"$group": {"_id": "$size", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}], "cursor": {}, "lsid": {"id": {"$binary": {"base64": "H4tLG7+9SPiyukZ8sfmfXg==", "subType": "04"}}}, "$clusterTime": {"clusterTime": {"$timestamp": {"t": 1758720076, "i": 1}}, "signature": {"hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}}, "keyId": 0}}, "$readPreference": {"mode": "primaryPreferred"}, "$db": "test"}, "planSummary": "COLLSCAN", "keysExamined": 0, "docsExamined": 7, "hasSortStage": true, "cursorExhausted": true, "numYields": 0, "nreturned": 3, "queryHash": "BA2D5E3A", "planCacheKey": "69EA54FF", "reslen": 328, "locks": {"FeatureCompatibilityVersion": {"acquireCount": {"r": 2}}, "Global": {"acquireCount": {"r": 2}}, "Mutex": {"acquireCount": {"r": 2}}}, "readConcern": {"level": "local", "provenance": "implicitDefault"}, "writeConcern": {"w": "majority", "wtimeout": 0, "provenance": "implicitDefault"}, "storage": {}, "remote": "127.0.0.1:56678", "protocol": "op_msg", "durationMillis": 0}}')
slow_cmd = json_utils.loads('{"t":{"$date":"2025-09-24T16:46:17.078+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn53","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"createIndexes":"pizzas","indexes":[{"name":"type_1","key":{"type":1}}],"lsid":{"id":{"$uuid":"ee544a5a-d47b-4ee5-9ca1-f2859e69a650"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758725176,"i":7}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"numYields":0,"reslen":271,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":3}},"FeatureCompatibilityVersion":{"acquireCount":{"r":3,"w":2}},"ReplicationStateTransition":{"acquireCount":{"w":5}},"Global":{"acquireCount":{"r":3,"w":2}},"Database":{"acquireCount":{"r":2,"w":1}},"Collection":{"acquireCount":{"r":2,"W":1}},"Mutex":{"acquireCount":{"r":3}}},"flowControl":{"acquireCount":2,"timeAcquiringMicros":2},"readConcern":{"level":"local","provenance":"implicitDefault"},"writeConcern":{"w":"majority","wtimeout":0,"provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:49701","protocol":"op_msg","durationMillis":213}}')
slow_getmore = json_utils.loads('{"t":{"$date":"2025-09-24T16:46:17.089+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn53","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.pizzas","appName":"mongosh 2.5.6","command":{"getMore":2225429849964214763,"collection":"pizzas","batchSize":1,"lsid":{"id":{"$uuid":"ee544a5a-d47b-4ee5-9ca1-f2859e69a650"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758725177,"i":2}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"originatingCommand":{"find":"pizzas","filter":{"size":{"$in":["small","medium","large"]}},"batchSize":1,"lsid":{"id":{"$uuid":"ee544a5a-d47b-4ee5-9ca1-f2859e69a650"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758725177,"i":2}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"planSummary":"COLLSCAN","cursorid":2225429849964214763,"keysExamined":0,"docsExamined":1,"numYields":0,"nreturned":1,"reslen":292,"locks":{"FeatureCompatibilityVersion":{"acquireCount":{"r":1}},"Global":{"acquireCount":{"r":1}},"Mutex":{"acquireCount":{"r":1}}},"readConcern":{"level":"local","provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:49701","protocol":"op_msg","durationMillis":0}}')

def test_query_analyzer():
    shape = analyze_query_shape(slow_insert)
    assert shape == {}
    shape = analyze_query_shape(slow_find)
    assert shape == {"size": 1}
    shape = analyze_query_shape(slow_aggregate)
    assert shape == {"size": {"$in": 1}}
    shape = analyze_query_shape(slow_cmd)
    assert shape == {}
    shape = analyze_query_shape(slow_getmore)
    assert shape == {"size": {"$in": 1}}


def test_query_to_shape():
    query = {"size": "medium"}
    shape = query_to_shape(query)
    assert shape == {"size": 1}

    query = {"age": {"$gt": 30}, "status": "A"}
    shape = query_to_shape(query)
    assert shape == {"age": {"$gt": 1}, "status": 1}

    query = {"tags": ["red", "blank"]}
    shape = query_to_shape(query)
    assert shape == {"tags": 1}

    query = {
        "items": {
            "$elemMatch": {
                "name": "item1",
                "price": {"$gt": 10}
            }
        }
    }
    shape = query_to_shape(query)
    assert shape == {"items": {"$elemMatch": {"name": 1, "price": {"$gt": 1}}}}

    query = {"$or": [ {"status": "A"}, {"qty": {"$lt": 30}} ]}
    shape = query_to_shape(query)
    assert shape == {"$or": [ {"status": 1}, {"qty": {"$lt": 1}} ]}

    query = {"$and": [ {"age": {"$gt": 25}}, {"$or": [{"age": {"$lt": 50}}, {"location": "USA"}]} ]}
    shape = query_to_shape(query)
    assert shape == {"$and": [ {"age": {"$gt": 1}}, {"$or": [{"age": {"$lt": 1}}, {"location": 1}]} ]}

    query = {}
    shape = query_to_shape(query)
    assert shape == {}