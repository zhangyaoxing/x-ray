from bson import json_util
from libs.log_analysis.log_items.wef_item import WEFItem
from tests.log.mocking import gen_mock_write_output

LOGS = [
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:49.656+02:00"},"s":"W",  "c":"ASIO",     "id":22601,   "ctx":"thread1","msg":"No TransportLayer configured during NetworkInterface startup"}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:49.659+02:00"},"s":"W",  "c":"ASIO",     "id":22601,   "ctx":"thread1","msg":"No TransportLayer configured during NetworkInterface startup"}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:50.184+02:00"},"s":"W",  "c":"CONTROL",  "id":22120,   "ctx":"initandlisten","msg":"Access control is not enabled for the database. Read and write access to data and configuration is unrestricted","tags":["startupWarnings"]}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:50.186+02:00"},"s":"W",  "c":"CONTROL",  "id":22140,   "ctx":"initandlisten","msg":"This server is bound to localhost. Remote systems will be unable to connect to this server. Start the server with --bind_ip <address> to specify which IP addresses it should serve responses from, or with --bind_ip_all to bind to all interfaces. If this behavior is desired, start the server with --bind_ip 127.0.0.1 to disable this warning","tags":["startupWarnings"]}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:50.188+02:00"},"s":"W",  "c":"CONTROL",  "id":22184,   "ctx":"initandlisten","msg":"Soft rlimits for open file descriptors too low","attr":{"currentValue":256,"recommendedMinimum":64000},"tags":["startupWarnings"]}'
    ),
]


def test_wef_item():
    item = WEFItem(output_folder="/tmp", config={})
    output, item._write_output = gen_mock_write_output(item)
    for log in LOGS:
        item.analyze(log)
    item.finalize_analysis()

    assert len(output) == 4
    result = output[0]
    assert result["id"] == 22601
    assert result["severity"] == "w"
    assert len(result["timestamp"]) == 2
    assert "No TransportLayer configured" in result["msg"]

    result = output[1]
    assert result["id"] == 22120
    assert result["severity"] == "w"
    assert len(result["timestamp"]) == 1
    assert "Access control is not enabled" in result["msg"]
