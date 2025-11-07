from datetime import datetime
from libs.healthcheck.shared import SEVERITY, to_json, str_to_md_id


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
