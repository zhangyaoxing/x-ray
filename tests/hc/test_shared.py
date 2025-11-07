from datetime import datetime
from bson import json_util
from libs.healthcheck.shared import SEVERITY, to_json, str_to_md_id, enum_all_nodes
from libs.utils import get_script_path


def test_to_json():
    s = SEVERITY.HIGH
    date = datetime(2025, 9, 25, 23, 39, 51, 220000)
    data = {
        "severity": "HIGH",
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
        level = kwargs.get("level")
        assert set_name == "mongos"
        assert level == "sh_cluster"
        assert nodes["type"] == "SH"
        assert "shard01" in nodes["map"]
        assert "shard02" in nodes["map"]
        assert "config" in nodes["map"]
        assert "mongos" in nodes["map"]

    def func_all_mongos(set_name, nodes, **kwargs):
        level = kwargs.get("level")
        assert set_name == "mongos"
        assert level == "all_mongos"
        assert len(nodes["members"]) == 2
        assert nodes["members"][0]["host"] == "M-QTFH0WFXLG:30017"
        assert nodes["members"][1]["host"] == "M-QTFH0WFXLG:30025"

    def func_mongos_member(set_name, nodes, **kwargs):
        level = kwargs.get("level")
        assert set_name == "mongos"
        assert level == "mongos_member"
        assert nodes["host"] in ["M-QTFH0WFXLG:30017", "M-QTFH0WFXLG:30025"]

    def func_shard(set_name, nodes, **kwargs):
        level = kwargs.get("level")
        assert set_name in ["shard01", "shard02"]
        assert level == "shard"
        assert len(nodes["members"]) == 3
        assert nodes["members"][0]["host"] == "localhost:30018"
        assert nodes["members"][1]["host"] == "localhost:30019"
        assert nodes["members"][2]["host"] == "localhost:30020"

    def func_shard_member(set_name, nodes, **kwargs):
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

    def func_config(set_name, nodes, **kwargs):
        level = kwargs.get("level")
        assert set_name == "configRepl"
        assert level == "config"
        assert len(nodes["members"]) == 1
        assert nodes["members"][0]["host"] == "localhost:30024"

    def func_config_member(set_name, nodes, **kwargs):
        level = kwargs.get("level")
        assert set_name == "configRepl"
        assert level == "config_member"
        assert nodes["host"] == "localhost:30024"

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
