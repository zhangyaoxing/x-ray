def test_load_config():
    from libs.utils import load_config

    config = load_config("config.json")
    assert "log" in config
    assert "healthcheck" in config


def test_truncate_content():
    from libs.utils import truncate_content

    content = "This is a test log message for truncation."
    truncated = truncate_content(content, max_words=5)
    assert truncated == "This is a test log ..."


def test_tooltip_html():
    from libs.utils import tooltip_html

    full = "This is the full content"
    truncated = "This is..."
    html = tooltip_html(full, truncated)
    assert 'data-tip="This is the full content"' in html
    assert ">This is...</span>" in html


def test_load_classes():
    from libs.utils import load_classes

    classes = load_classes("libs.log_analysis.log_items")
    assert "SlowChartItem" in classes
    assert "WEFItem" in classes


def test_format_size():
    from libs.utils import format_size

    assert format_size(1023) == "1023.00 B"
    assert format_size(2048) == "2.00 KB"
    assert format_size(5 * 1024 * 1024) == "5.00 MB"
    assert format_size(3 * 1024 * 1024 * 1024) == "3.00 GB"
    assert format_size(7 * 1024 * 1024 * 1024 * 1024) == "7.00 TB"
    assert format_size(9 * 1024 * 1024 * 1024 * 1024 * 1024) == "9.00 PB"


def test_escape_markdown():
    from libs.utils import escape_markdown

    text = "This_is*some`markdown|text<with>special_chars"
    escaped = escape_markdown(text)
    assert escaped == "This\\_is\\*some\\`markdown\\|text&lt;with&gt;special\\_chars"


def test_format_json_md():
    from libs.utils import format_json_md

    data = {"key": "value", "number": 123}
    md = format_json_md(data)
    assert md == '{<br>&nbsp;&nbsp;"key":&nbsp;"value",<br>&nbsp;&nbsp;"number":&nbsp;123<br>}'
    md = format_json_md(data, indent=0)
    assert md == '{"key": "value","number": 123}'


def test_to_ejson():
    from libs.utils import to_ejson
    from datetime import datetime
    from enum import Enum

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    data = {"color": Color.RED, "value": 42}
    json_str = to_ejson(data, indent=None)
    assert json_str == '{"color": "RED", "value": 42}'

    cls_maps = [{"class": datetime, "func": lambda o: o.isoformat()}]
    now = datetime.now()
    data = {"timestamp": now}
    json_str = to_ejson(data, indent=None, cls_maps=cls_maps)
    assert f'{{"timestamp": "{now.isoformat()}"}}' == json_str

    json_str = to_ejson({"a": 1, "b": 2})
    assert json_str == '{\n  "a": 1,\n  "b": 2\n}'

    json_str = to_ejson({"a": 1, "b": 2}, indent=4)
    assert json_str == '{\n    "a": 1,\n    "b": 2\n}'


def test_json_hash():
    from libs.utils import json_hash

    data = {"a": 1, "b": 2}
    hash1 = json_hash(data)
    assert hash1 == "EC55C9EC4B598E6F"
    hash2 = json_hash(data, digest_size=4)
    assert hash2 == "C5F6113B"
