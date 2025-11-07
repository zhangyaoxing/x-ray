from bson import json_util
from libs.log_analysis.log_items.state_trace_item import StateTraceItem
from tests.log.mocking import gen_mock_write_output

LOGS = [
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:49.668+02:00"},"s":"I",  "c":"CONTROL",  "id":4615611, "ctx":"initandlisten","msg":"MongoDB starting","attr":{"pid":59817,"port":27017,"dbPath":"/Users/yaoxing.zhang/Workspace/MongoDB/rs_5.0.14/data/replset/rs1/db","architecture":"64-bit","host":"M-QTFH0WFXLG"}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:50.359+02:00"},"s":"I",  "c":"REPL",     "id":21392,   "ctx":"ReplCoord-0","msg":"New replica set config in use","attr":{"config":{"_id":"replset","version":1,"term":3,"members":[{"_id":0,"host":"localhost:27017","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":1,"tags":{},"secondaryDelaySecs":0,"votes":1},{"_id":1,"host":"localhost:27018","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":1,"tags":{},"secondaryDelaySecs":0,"votes":1},{"_id":2,"host":"localhost:27019","arbiterOnly":false,"buildIndexes":true,"hidden":false,"priority":1,"tags":{},"secondaryDelaySecs":0,"votes":1}],"protocolVersion":1,"writeConcernMajorityJournalDefault":true,"settings":{"chainingAllowed":true,"heartbeatIntervalMillis":2000,"heartbeatTimeoutSecs":10,"electionTimeoutMillis":10000,"catchUpTimeoutMillis":-1,"catchUpTakeoverDelayMillis":30000,"getLastErrorModes":{},"getLastErrorDefaults":{"w":1,"wtimeout":0},"replicaSetId":{"$oid":"6784fe50cedf1b22edae209f"}}}}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:51.224+02:00"},"s":"I",  "c":"REPL",     "id":21215,   "ctx":"ReplCoord-0","msg":"Member is in new state","attr":{"hostAndPort":"localhost:27018","newState":"STARTUP2"}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:50.374+02:00"},"s":"I",  "c":"REPL",     "id":21216,   "ctx":"ReplCoord-3","msg":"Member is now in state RS_DOWN","attr":{"hostAndPort":"localhost:27019","heartbeatMessage":"Error connecting to localhost:27019 (127.0.0.1:27019) :: caused by :: Connection refused"}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:40:59.827+02:00"},"s":"I",  "c":"REPL",     "id":21358,   "ctx":"ReplCoord-5","msg":"Replica set state transition","attr":{"newState":"PRIMARY","oldState":"SECONDARY"}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:40:59.769+02:00"},"s":"I",  "c":"ELECTION", "id":4615660, "ctx":"ReplCoord-5","msg":"Starting an election for a priority takeover"}'
    ),
]


def test_state_trace_item():
    item = StateTraceItem(output_folder="/tmp", config={})
    output, item._write_output = gen_mock_write_output(item)
    for log in LOGS:
        item.analyze(log)
    item.finalize_analysis()

    assert len(output[0]) == 3

    result = output[0]["M-QTFH0WFXLG:27017"]
    assert len(result) == 4
    assert result[0]["id"] == 21392
    assert result[0]["event"] == "NewConfig"
    assert result[0]["host"] == "M-QTFH0WFXLG:27017"
    assert result[1]["id"] == 21358
    assert result[1]["event"] == "StateTransition"
    assert result[2]["id"] == 4615660
    assert result[2]["event"] == "PriorityTakeover"

    result = output[0]["localhost:27018"]
    assert len(result) == 2
    assert result[0]["id"] == 21215
    assert result[0]["event"] == "NewMemberState"
    assert result[0]["host"] == "localhost:27018"
    assert result[0]["details"]["new_state"] == "STARTUP2"

    result = output[0]["localhost:27019"]
    assert len(result) == 2
    assert result[0]["id"] == 21216
    assert result[0]["event"] == "NewMemberState"
    assert result[0]["host"] == "localhost:27019"
    assert result[0]["details"]["new_state"] == "DOWN"
