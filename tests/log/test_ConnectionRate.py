from bson import json_util
from libs.log_analysis.log_items.connection_rate_item import ConnectionRateItem

LOGS = [
    json_util.loads('{"t":{"$date":"2025-09-25T23:39:51.199+02:00"},"s":"I",  "c":"NETWORK",  "id":22943,   "ctx":"listener","msg":"Connection accepted","attr":{"remote":"127.0.0.1:51011","uuid":"3c5442e1-7747-4463-975a-c02dfc39fcfb","connectionId":1,"connectionCount":1}}'),
    json_util.loads('{"t":{"$date":"2025-09-25T23:39:51.204+02:00"},"s":"I",  "c":"NETWORK",  "id":22944,   "ctx":"conn1","msg":"Connection ended","attr":{"remote":"127.0.0.1:51011","uuid":"3c5442e1-7747-4463-975a-c02dfc39fcfb","connectionId":1,"connectionCount":0}}'),
    json_util.loads('{"t":{"$date":"2025-09-25T23:39:51.218+02:00"},"s":"I",  "c":"NETWORK",  "id":22943,   "ctx":"listener","msg":"Connection accepted","attr":{"remote":"127.0.0.1:51013","uuid":"08880c06-5e07-494f-879f-5c7c24af578a","connectionId":3,"connectionCount":2}}'),
    json_util.loads('{"t":{"$date":"2025-09-26T00:02:01.718+02:00"},"s":"I",  "c":"NETWORK",  "id":22943,   "ctx":"listener","msg":"Connection accepted","attr":{"remote":"127.0.0.1:57335","uuid":"8d98ce07-0fe0-4543-b69b-8aa23d175a6c","connectionId":55,"connectionCount":20}}'),
    json_util.loads('{"t":{"$date":"2025-09-26T00:03:01.718+02:00"},"s":"I",  "c":"NETWORK",  "id":22943,   "ctx":"listener","msg":"Connection accepted","attr":{"remote":"127.0.0.1:57335","uuid":"8d98ce07-0fe0-4543-b69b-8aa23d175a6c","connectionId":55,"connectionCount":20}}'),
]

def test_connection_rate_item():
    item = ConnectionRateItem(output_folder="/tmp", config={})
    output = []
    item._write_output = lambda: output.append(item._cache.copy())
    for log in LOGS:
        item.analyze(log)

    assert len(output) == 2
    result = output[0]
    assert "time" in result
    assert result["time"].isoformat() == "2025-09-25T21:39:00"
    assert result["created"] == 2
    assert result["ended"] == 1
    assert result["total"] == 2
    assert result["byIp"]["127.0.0.1"]["created"] == 2
    assert result["byIp"]["127.0.0.1"]["ended"] == 1

    result = output[1]
    assert "time" in result
    assert result["time"].isoformat() == "2025-09-25T22:02:00"
    assert result["created"] == 1
    assert result["ended"] == 0
    assert result["total"] == 20
    assert result["byIp"]["127.0.0.1"]["created"] == 1
    assert result["byIp"]["127.0.0.1"]["ended"] == 0