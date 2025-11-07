import json
from bson import json_util
from libs.log_analysis.log_items.client_meta_item import (
    ClientMetaItem,
    parse_version_from_log,
    COMPATIBILITY_MATRIX_JSON,
    is_driver_compatible,
)
from tests.log.mocking import gen_mock_write_output
from libs.version import Version

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


LOGS_2 = [
    {"name": "NetworkInterfaceTL", "version": "5.0.31"},
    {"name": "mongo-csharp-driver", "version": "2.21.0.0"},
    {"name": "mongo-java-driver|sync", "version": "3.12.10"},
    {"name": "mongoc / mongocxx", "version": "1.26.3 / 3.8.1"},
    {
        "name": "mongoc / ext-mongodb:PHP / PHPLIB/symfony-mongodb ",
        "version": "1.25.2 / 1.17.2 / 1.17.0/2.6.1 ",
    },
    {"name": "mongo-java-driver|mongo-scala-driver", "version": "unknown|2.3.0"},
    {"name": "mongo-go-driver", "version": "v1.12.0-cloud"},
]


def test_version_parser():
    target_drivers = [
        "NetworkInterfaceTL",
        "mongo-csharp-driver",
        "mongo-java-driver",
        "mongocxx",
        "ext-mongodb:PHP",
        "mongo-scala-driver",
        "mongo-go-driver",
    ]
    expected_versions = [
        "5.0.31",
        "2.21.0.0",
        "3.12.10",
        "3.8.1",
        "1.17.2",
        "2.3.0",
        "1.12.0",
    ]
    for log, target_driver, expected_version in zip(LOGS_2, target_drivers, expected_versions):
        parsed_version = parse_version_from_log(log["name"], log["version"], target_driver)
        assert parsed_version == Version.parse(
            expected_version
        ), f"Expected {expected_version}, got {parsed_version} for driver {target_driver}"


def test_is_driver_compatible():
    # Assume server version is 7.0.0 for testing
    server_version = Version.parse("7.0.0")
    with open(COMPATIBILITY_MATRIX_JSON, "r") as f:
        compatibility_matrix = json.load(f)
    matrix_70 = {k: Version(v) for k, v in compatibility_matrix.get("7.0", {}).items()}
    expected_compatibility = [True, True, False, True, True, False, True]
    for log, expected in zip(LOGS_2, expected_compatibility):
        is_compatible = is_driver_compatible(log["name"], log["version"], server_version, matrix_70)
        assert (
            is_compatible == expected
        ), f"Expected compatibility {expected} for driver {log['name']}, got {is_compatible}"
