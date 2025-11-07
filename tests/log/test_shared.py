from datetime import datetime
from libs.version import Version
from libs.log_analysis.shared import to_json


def test_to_json():
    dt = datetime(2024, 6, 1, 12, 30, 45)
    v = Version.parse("1.2.3")
    obj = {"timestamp": dt, "message": "Test log", "version": v}
    json_str = to_json(obj)
    assert (
        json_str
        == '{"timestamp": "2024-06-01T12:30:45", "message": "Test log", "version": "1.2.3"}'
    )
    json_str_indented = to_json(obj, indent=2)
    expected_indented = """{
  "timestamp": "2024-06-01T12:30:45",
  "message": "Test log",
  "version": "1.2.3"
}"""
    assert json_str_indented == expected_indented
