from libs.log_analysis.log_items.client_meta_item import *

logs = [
    {"name": "NetworkInterfaceTL", "version": "5.0.31"},
    {"name": "mongo-csharp-driver", "version": "2.21.0.0"},
    {"name": "mongo-java-driver|sync", "version": "3.12.10"},
    {"name": "mongoc / mongocxx", "version": "1.26.3 / 3.8.1"},
    {"name": "mongoc / ext-mongodb:PHP / PHPLIB/symfony-mongodb ", "version": "1.25.2 / 1.17.2 / 1.17.0/2.6.1 "},
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
    expected_versions = ["5.0.31", "2.21.0.0", "3.12.10", "3.8.1", "1.17.2", "2.3.0", "1.12.0"]
    for log, target_driver, expected_version in zip(logs, target_drivers, expected_versions):
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
    for log, expected in zip(logs, expected_compatibility):
        is_compatible = is_driver_compatible(log["name"], log["version"], server_version, matrix_70)
        assert (
            is_compatible == expected
        ), f"Expected compatibility {expected} for driver {log['name']}, got {is_compatible}"
