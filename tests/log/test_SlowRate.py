from bson import json_util
from libs.log_analysis.log_items.slow_rate_item import SlowRateItem
from tests.log.mocking import gen_mock_write_output

LOGS = [
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:40:10.414+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn20","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.$cmd","appName":"mongosh 2.5.6","command":{"listCollections":1,"filter":{},"cursor":{},"nameOnly":true,"authorizedCollections":false,"lsid":{"id":{"$uuid":"4541f695-c7dd-45c9-97a6-ee9ed1d10960"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758836335,"i":1}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"numYields":0,"reslen":291,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":1}},"FeatureCompatibilityVersion":{"acquireCount":{"r":1}},"Global":{"acquireCount":{"r":1}},"Mutex":{"acquireCount":{"r":1}}},"readConcern":{"level":"local","provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:51082","protocol":"op_msg","durationMillis":0}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:40:23.646+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn26","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","appName":"mongosh 2.5.6","command":{"ismaster":1,"helloOk":true,"client":{"application":{"name":"mongosh 2.5.6"},"driver":{"name":"nodejs|mongosh","version":"6.17.0|2.5.6"},"platform":"Node.js v24.4.1, LE","os":{"name":"darwin","architecture":"arm64","version":"24.6.0","type":"Darwin"}},"compression":["none"],"$db":"admin"},"numYields":0,"reslen":783,"locks":{},"remote":"127.0.0.1:51204","protocol":"op_query","durationMillis":4}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:41:00.349+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn3","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","command":{"replSetHeartbeat":"replset","configVersion":90188,"configTerm":-1,"hbv":1,"from":"localhost:27018","fromId":1,"term":6,"primaryId":0,"maxTimeMSOpOnly":10000,"$replData":1,"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758836459,"i":1}},"signature":{"hash":{"$binary":{"base64":"LcjvzFIcAYzwWmqus7gL7ErDghM=","subType":"0"}},"keyId":7553643405352370178}},"$db":"admin"},"numYields":0,"reslen":650,"locks":{},"remote":"127.0.0.1:51013","protocol":"op_msg","durationMillis":0}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:41:00.854+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn3","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","command":{"replSetHeartbeat":"replset","configVersion":90188,"configTerm":-1,"hbv":1,"from":"localhost:27018","fromId":1,"term":6,"primaryId":0,"maxTimeMSOpOnly":10000,"$replData":1,"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758836459,"i":2}},"signature":{"hash":{"$binary":{"base64":"LcjvzFIcAYzwWmqus7gL7ErDghM=","subType":"0"}},"keyId":7553643405352370178}},"$db":"admin"},"numYields":0,"reslen":650,"locks":{},"remote":"127.0.0.1:51013","protocol":"op_msg","durationMillis":0}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:41:00.860+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn35","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","command":{"isMaster":1,"client":{"driver":{"name":"NetworkInterfaceTL","version":"5.0.14"},"os":{"type":"Darwin","name":"Mac OS X","architecture":"x86_64","version":"24.6.0"}},"compression":["snappy","zstd","zlib"],"internalClient":{"minWireVersion":13,"maxWireVersion":13},"hangUpOnStepDown":false,"saslSupportedMechs":"local.__system","$db":"admin"},"numYields":0,"reslen":878,"locks":{},"remote":"127.0.0.1:51366","protocol":"op_query","durationMillis":5}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:56:24.802+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn26","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","appName":"mongosh 2.5.6","command":{"listDatabases":1,"lsid":{"id":{"$uuid":"eef6660c-6ef9-4492-a285-fab357f0b335"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758836465,"i":15}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"admin"},"numYields":0,"reslen":585,"locks":{"ParallelBatchWriterMode":{"acquireCount":{"r":8}},"FeatureCompatibilityVersion":{"acquireCount":{"r":8}},"ReplicationStateTransition":{"acquireCount":{"w":8}},"Global":{"acquireCount":{"r":8}},"Database":{"acquireCount":{"r":7}},"Collection":{"acquireCount":{"r":24}},"Mutex":{"acquireCount":{"r":7}},"oplog":{"acquireCount":{"r":1}}},"readConcern":{"level":"local","provenance":"implicitDefault"},"storage":{},"remote":"127.0.0.1:51204","protocol":"op_msg","durationMillis":1}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:56:24.805+02:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn28","msg":"Slow query","attr":{"type":"command","ns":"Restaurant.$cmd","appName":"mongosh 2.5.6","command":{"profile":0,"slowms":0,"lsid":{"id":{"$uuid":"9312b172-7afe-4990-ae1d-429f883088c7"}},"$clusterTime":{"clusterTime":{"$timestamp":{"t":1758836459,"i":2}},"signature":{"hash":{"$binary":{"base64":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=","subType":"0"}},"keyId":0}},"$readPreference":{"mode":"primaryPreferred"},"$db":"Restaurant"},"numYields":0,"reslen":204,"locks":{"FeatureCompatibilityVersion":{"acquireCount":{"w":1}},"ReplicationStateTransition":{"acquireCount":{"w":1}},"Global":{"acquireCount":{"w":1}},"Database":{"acquireCount":{"w":1}},"Mutex":{"acquireCount":{"r":1}}},"readConcern":{"level":"local","provenance":"implicitDefault"},"remote":"127.0.0.1:51206","protocol":"op_msg","durationMillis":3}}'
    ),
]


def test_slow_rate_item():
    item = SlowRateItem(output_folder="/tmp", config={})
    output, item._write_output = gen_mock_write_output(item)
    for log in LOGS:
        item.analyze(log)
    item.finalize_analysis()

    assert len(output) == 3
    result = output[0]
    assert "time" in result
    assert result["time"].isoformat() == "2025-09-25T21:40:00"
    assert result["total_slow_ms"] == 4
    assert result["count"] == 2

    result = output[1]
    assert "time" in result
    assert result["time"].isoformat() == "2025-09-25T21:41:00"
    assert result["total_slow_ms"] == 5
    assert result["count"] == 3

    result = output[2]
    assert "time" in result
    assert result["time"].isoformat() == "2025-09-25T21:56:00"
    assert result["total_slow_ms"] == 4
    assert result["count"] == 2
