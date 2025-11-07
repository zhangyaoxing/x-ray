from bson import json_util
from libs.log_analysis.log_items.client_meta_item import ClientMetaItem
from tests.log.mocking import gen_mock_write_output

LOGS = [
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:51.220+02:00"},"s":"I",  "c":"NETWORK",  "id":51800,   "ctx":"conn3","msg":"client metadata","attr":{"remote":"192.168.0.1:51013","client":"conn3","doc":{"driver":{"name":"NetworkInterfaceTL","version":"5.0.14"},"os":{"type":"Darwin","name":"Mac OS X","architecture":"x86_64","version":"24.6.0"}}}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:51.993+02:00"},"s":"I",  "c":"NETWORK",  "id":51800,   "ctx":"conn5","msg":"client metadata","attr":{"remote":"192.168.0.2:51028","client":"conn5","doc":{"driver":{"name":"PyMongo|c","version":"4.14.1"},"os":{"type":"Darwin","name":"Darwin","architecture":"arm64","version":"15.7"},"platform":"CPython 3.11.12.final.0","application":{"name":"mlaunch v1.7.2"}}}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:51.998+02:00"},"s":"I",  "c":"NETWORK",  "id":51800,   "ctx":"conn6","msg":"client metadata","attr":{"remote":"192.168.0.2:51031","client":"conn6","doc":{"driver":{"name":"PyMongo|c","version":"4.14.1"},"os":{"type":"Darwin","name":"Darwin","architecture":"arm64","version":"15.7"},"platform":"CPython 3.11.12.final.0","application":{"name":"mlaunch v1.7.2"}}}}'
    ),
    json_util.loads(
        '{"t":{"$date":"2025-09-25T23:39:52.000+02:00"},"s":"I",  "c":"NETWORK",  "id":51800,   "ctx":"conn8","msg":"client metadata","attr":{"remote":"192.168.0.3:51032","client":"conn8","doc":{"driver":{"name":"PyMongo|c","version":"4.14.1"},"os":{"type":"Darwin","name":"Darwin","architecture":"arm64","version":"15.7"},"platform":"CPython 3.11.12.final.0","application":{"name":"mlaunch v1.7.2"}}}}'
    ),
]


def test_client_metadata_item():
    item = ClientMetaItem(output_folder="/tmp", config={})
    output, item._write_output = gen_mock_write_output(item)
    for log in LOGS:
        item.analyze(log)
    item.finalize_analysis()

    assert len(output) == 2
    result = output[0]
    assert result["doc"]["driver"]["name"] == "NetworkInterfaceTL"
    assert result["ips"][0]["ip"] == "192.168.0.1"
    assert result["ips"][0]["count"] == 1

    result = output[1]
    assert result["doc"]["driver"]["name"] == "PyMongo|c"
    assert result["ips"][0]["ip"] == "192.168.0.2"
    assert result["ips"][0]["count"] == 2
    assert result["ips"][1]["ip"] == "192.168.0.3"
    assert result["ips"][1]["count"] == 1
