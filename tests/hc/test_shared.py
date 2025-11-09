from datetime import datetime
from bson import json_util
import pytest
from libs.healthcheck.shared import SEVERITY, to_json, str_to_md_id, enum_all_nodes, enum_result_items
from libs.utils import get_script_path


def test_to_json():
    s = SEVERITY.HIGH
    date = datetime(2025, 9, 25, 23, 39, 51, 220000)
    data = {
        "severity": s,
        "timestamp": date,
    }
    assert to_json(data) == '{\n"severity": "HIGH",\n"timestamp": "2025-09-25T23:39:51.220000"\n}'
    assert to_json(data, indent=2) == '{\n  "severity": "HIGH",\n  "timestamp": "2025-09-25T23:39:51.220000"\n}'
    assert to_json(data, indent=None) == '{"severity": "HIGH", "timestamp": "2025-09-25T23:39:51.220000"}'


def test_str_to_md_id():
    assert str_to_md_id("Test Title") == "test-title"
    assert str_to_md_id("Another Test Title") == "another-test-title"
    assert str_to_md_id("Title with Special_Characters!*&^%$#@") == "title-with-special_characters"
    assert str_to_md_id("  Leading and Trailing Spaces  ") == "leading-and-trailing-spaces"
    assert str_to_md_id("Mixed CASE Title") == "mixed-case-title"


def test_enum_all_nodes_sh():
    nodes = None
    with open(
        get_script_path("misc/example_data_structure/healthcheck/discovered_sh.json"), "r", encoding="utf-8"
    ) as f:
        nodes = json_util.loads(f.read())

    def func_sh_cluster(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "mongos"
            assert level == "sh_cluster"
            assert nodes["type"] == "SH"
            assert "shard01" in nodes["map"]
            assert "shard02" in nodes["map"]
            assert "config" in nodes["map"]
            assert "mongos" in nodes["map"]
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    def func_all_mongos(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "mongos"
            assert level == "all_mongos"
            assert len(nodes["members"]) == 2
            assert nodes["members"][0]["host"] == "M-QTFH0WFXLG:30017"
            assert nodes["members"][1]["host"] == "M-QTFH0WFXLG:30028"
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_mongos_members = []

    def func_mongos_member(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "mongos"
            assert level == "mongos_member"
            assert nodes["host"] in ["M-QTFH0WFXLG:30017", "M-QTFH0WFXLG:30028"]
            enumed_mongos_members.append(nodes["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    def func_shard(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name in ["shard01", "shard02"]
            assert level == "shard"
            assert len(nodes["members"]) == 3
            if set_name == "shard01":
                assert nodes["members"][0]["host"] == "localhost:30018"
                assert nodes["members"][1]["host"] == "localhost:30019"
                assert nodes["members"][2]["host"] == "localhost:30020"
            elif set_name == "shard02":
                assert nodes["members"][0]["host"] == "localhost:30021"
                assert nodes["members"][1]["host"] == "localhost:30022"
                assert nodes["members"][2]["host"] == "localhost:30023"
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_shard_members = []

    def func_shard_member(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name in ["shard01", "shard02"]
            assert level == "shard_member"
            assert nodes["host"] in [
                "localhost:30018",
                "localhost:30019",
                "localhost:30020",
                "localhost:30021",
                "localhost:30022",
                "localhost:30023",
            ]
            enumed_shard_members.append(nodes["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    def func_config(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "configRepl"
            assert level == "config"
            assert len(nodes["members"]) == 1
            assert nodes["members"][0]["host"] == "localhost:30024"
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_config_members = []

    def func_config_member(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "configRepl"
            assert level == "config_member"
            assert nodes["host"] == "localhost:30024"
            enumed_config_members.append(nodes["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    # Each test function must try/catch and raise pytest.fail on error to report properly
    # Because inside enum_all_nodes, exceptions are swallowed to allow continuing enumeration
    enum_all_nodes(
        nodes,
        func_sh_cluster=func_sh_cluster,
        func_all_mongos=func_all_mongos,
        func_mongos_member=func_mongos_member,
        func_shard=func_shard,
        func_shard_member=func_shard_member,
        func_config=func_config,
        func_config_member=func_config_member,
    )
    assert set(enumed_mongos_members) == {"M-QTFH0WFXLG:30017", "M-QTFH0WFXLG:30028"}
    assert set(enumed_shard_members) == {
        "localhost:30018",
        "localhost:30019",
        "localhost:30020",
        "localhost:30021",
        "localhost:30022",
        "localhost:30023",
    }
    assert set(enumed_config_members) == {"localhost:30024"}


def test_enum_all_nodes_rs():
    nodes = None
    with open(
        get_script_path("misc/example_data_structure/healthcheck/discovered_rs.json"), "r", encoding="utf-8"
    ) as f:
        nodes = json_util.loads(f.read())

    def func_rs_cluster(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "replset"
            assert level == "rs_cluster"
            assert nodes["type"] == "RS"
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_nodes = []

    def func_rs_member(set_name, nodes, **kwargs):
        try:
            level = kwargs.get("level")
            assert set_name == "replset"
            assert level == "rs_member"
            host = nodes["host"]
            assert host in ["localhost:27017", "localhost:27018", "localhost:27019"]
            enumed_nodes.append(host)
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    # Each test function must try/catch and raise pytest.fail on error to report properly
    # Because inside enum_all_nodes, exceptions are swallowed to allow continuing enumeration
    enum_all_nodes(
        nodes,
        func_rs_cluster=func_rs_cluster,
        func_rs_member=func_rs_member,
    )
    assert set(enumed_nodes) == {"localhost:27017", "localhost:27018", "localhost:27019"}


def test_enum_result_items_rs():
    result = None
    with open(get_script_path("misc/example_data_structure/healthcheck/result_rs.json"), "r", encoding="utf-8") as f:
        result = json_util.loads(f.read())

    def func_rs_cluster(name, node, **kwargs):
        try:
            assert name == "replset"
            assert node["type"] == "RS"
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_rs_members = []

    def func_rs_member(name, node, **kwargs):
        try:
            level = kwargs.get("level")
            assert name == "replset"
            assert level == "rs_member"
            assert node["host"] in ["localhost:27017", "localhost:27018", "localhost:27019"]
            assert node["rawResult"]["ok"] == 1
            assert node["rawResult"]["versionArray"] == [5, 0, 14, 0]
            enumed_rs_members.append(node["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    # Each test function must try/catch and raise pytest.fail on error to report properly
    # Because inside enum_result_items, exceptions are swallowed to allow continuing enumeration
    enum_result_items(
        result,
        func_rs_cluster=func_rs_cluster,
        func_rs_member=func_rs_member,
    )
    assert set(enumed_rs_members) == {"localhost:27017", "localhost:27018", "localhost:27019"}


def test_enum_result_items_sh():
    result = None
    with open(get_script_path("misc/example_data_structure/healthcheck/result_sh.json"), "r", encoding="utf-8") as f:
        result = json_util.loads(f.read())

    def func_sh_cluster(name, node, **kwargs):
        try:
            level = kwargs.get("level")
            assert level == "sh_cluster"
            assert node["type"] == "SH"
            assert "shard01" in node["map"]
            assert "shard02" in node["map"]
            assert "config" in node["map"]
            assert "mongos" in node["map"]
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_mongos_members = []

    def func_mongos_member(name, node, **kwargs):
        try:
            assert name == "mongos"
            level = kwargs.get("level")
            assert level == "mongos_member"
            assert node["host"] in ["M-QTFH0WFXLG:30017", "M-QTFH0WFXLG:30028"]
            if node["host"] == "M-QTFH0WFXLG:30017":
                assert node["rawResult"]["ok"] == 1
            elif node["host"] == "M-QTFH0WFXLG:30028":
                assert node["rawResult"] is None
            enumed_mongos_members.append(node["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    def func_shard(name, node, **kwargs):
        try:
            level = kwargs.get("level")
            assert level == "shard"
            assert name in ["shard01", "shard02"]
            assert node["rawResult"] is None
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_shard_members = []

    def func_shard_member(name, node, **kwargs):
        try:
            level = kwargs.get("level")
            assert level == "shard_member"
            assert name in ["shard01", "shard02"]
            assert node["host"] in [
                "localhost:30018",
                "localhost:30019",
                "localhost:30020",
                "localhost:30021",
                "localhost:30022",
                "localhost:30023",
            ]
            enumed_shard_members.append(node["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    def func_config(name, node, **kwargs):
        try:
            level = kwargs.get("level")
            assert level == "config"
            assert name == "configRepl"
            assert node["rawResult"] is None
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    enumed_config_members = []

    def func_config_member(name, node, **kwargs):
        try:
            level = kwargs.get("level")
            assert level == "config_member"
            assert name == "configRepl"
            assert node["host"] == "localhost:30024"
            enumed_config_members.append(node["host"])
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
        return None, None

    # Each test function must try/catch and raise pytest.fail on error to report properly
    # Because inside enum_result_items, exceptions are swallowed to allow continuing enumeration
    enum_result_items(
        result,
        func_sh_cluster=func_sh_cluster,
        func_mongos_member=func_mongos_member,
        func_shard=func_shard,
        func_shard_member=func_shard_member,
        func_config=func_config,
        func_config_member=func_config_member,
    )
    assert set(enumed_mongos_members) == {"M-QTFH0WFXLG:30017", "M-QTFH0WFXLG:30028"}
    assert set(enumed_shard_members) == {
        "localhost:30018",
        "localhost:30019",
        "localhost:30020",
        "localhost:30021",
        "localhost:30022",
        "localhost:30023",
    }
    assert set(enumed_config_members) == {"localhost:30024"}
