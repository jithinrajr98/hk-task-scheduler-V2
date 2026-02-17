import json
import pytest

from app import filter_by_day, get_task_color, validate_constraints, TASK_COLORS
from prompt import parse_response


# --- filter_by_day ---

SAMPLE_SCHEDULE = [
    {"name": "Alice", "day": "Monday", "shift_name": "shift_1", "start_time": "07:00", "end_time": "15:00"},
    {"name": "Bob", "day": "Monday", "shift_name": "shift_2", "start_time": "13:00", "end_time": "21:00"},
    {"name": "Carol", "day": "Monday", "shift_name": "shift_1", "start_time": "07:00", "end_time": "15:00"},
    {"name": "Alice", "day": "Tuesday", "shift_name": "shift_1", "start_time": "07:00", "end_time": "15:00"},
]


def test_filter_by_day_correct_day():
    result = filter_by_day(SAMPLE_SCHEDULE, "Monday")
    assert len(result) == 3
    assert {s["name"] for s in result} == {"Alice", "Bob", "Carol"}


def test_filter_by_day_no_match():
    result = filter_by_day(SAMPLE_SCHEDULE, "Sunday")
    assert result == []


# --- parse_response ---

def test_parse_response_with_tags():
    text = '<response>{"assignments": [{"employee": "A", "tasks": {"07:00": "Floor_1"}}]}</response>'
    result = parse_response(text)
    assert result is not None
    assert "assignments" in result
    assert result["assignments"][0]["employee"] == "A"


def test_parse_response_raw_json():
    text = '{"assignments": []}'
    result = parse_response(text)
    assert result == {"assignments": []}


def test_parse_response_with_surrounding_text():
    text = 'Here is the schedule:\n<response>\n{"assignments": [{"employee": "B", "tasks": {}}]}\n</response>\nDone.'
    result = parse_response(text)
    assert result is not None
    assert result["assignments"][0]["employee"] == "B"


def test_parse_response_malformed():
    result = parse_response("not json at all")
    assert result is None


def test_parse_response_with_think_tags():
    text = '<response><think>Let me analyze {this} carefully...</think>{"assignments": [{"employee": "A", "tasks": {"07:00": "Floor_1"}}]}</response>'
    result = parse_response(text)
    assert result is not None
    assert result["assignments"][0]["employee"] == "A"


# --- validate_constraints ---

VALID_ASSIGNMENTS = [
    {"employee": "A", "tasks": {"07:00": "Floor_2", "08:00": "Floor_2", "09:00": "Outdoor - DP", "10:00": "Egress", "11:00": "Egress", "12:00": "Break", "13:00": "Float_1", "14:00": "BOH-Breakroom"}},
    {"employee": "B", "tasks": {"07:00": "Floor_2", "08:00": "Floor_2", "09:00": "Outdoor - Hallway", "10:00": "Egress", "11:00": "Egress", "12:00": "Break", "13:00": "Float_-1", "14:00": "BOH-Restrooms"}},
    {"employee": "C", "tasks": {"07:00": "Floor_0", "08:00": "Floor_0", "09:00": "Outdoor - Main Gate", "10:00": "BOH-Breakroom", "11:00": "Break", "12:00": "Restroom_2", "13:00": "Restroom_2", "14:00": "Restroom_2"}},
    {"employee": "D", "tasks": {"07:00": "Floor_1", "08:00": "Floor_1", "09:00": "Outdoor - SideHallway", "10:00": "BOH-Restrooms", "11:00": "Break", "12:00": "Restroom_4", "13:00": "Restroom_4", "14:00": "Restroom_4"}},
    {"employee": "E", "tasks": {"07:00": "Floor_-1", "08:00": "Floor_3", "09:00": "Outdoor - DP", "10:00": "Float_All", "11:00": "Restroom_2", "12:00": "Break", "13:00": "Float_0", "14:00": "Restroom_2"}},
    {"employee": "F", "tasks": {"07:00": "Floor_4", "08:00": "Floor_4", "09:00": "Outdoor - SideHallway", "10:00": "Restroom_4", "11:00": "Break", "12:00": "Float_ALL", "13:00": "Restroom_2", "14:00": "Restroom_2"}},
    {"employee": "G", "tasks": {"13:00": "Float_0", "14:00": "Float_1", "15:00": "Outside", "16:00": "Break", "17:00": "Float_-1", "18:00": "Restroom_2", "19:00": "Restroom_2", "20:00": "Float_TRELLO"}},
    {"employee": "H", "tasks": {"15:00": "Restroom_2", "16:00": "Restroom_2", "17:00": "BOH-Restrooms", "18:00": "BOH-Breakroom", "19:00": "Break", "20:00": "Restroom_2", "21:00": "Restroom_2", "22:00": "Restroom_2"}},
    {"employee": "I", "tasks": {"13:00": "Restroom_4", "14:00": "Restroom_4", "15:00": "Restroom_4", "16:00": "Restroom_4", "17:00": "Break", "18:00": "Restroom_4", "19:00": "Restroom_4", "20:00": "Restroom_4", "21:00": "Restroom_4", "22:00": "Restroom_4"}},
]


def test_validate_no_double_booking():
    results = validate_constraints(VALID_ASSIGNMENTS)
    no_db = next(r for r in results if r["rule"] == "No double-booking")
    assert no_db["pass"] is True


def test_validate_egress():
    results = validate_constraints(VALID_ASSIGNMENTS)
    egress = next(r for r in results if "Egress" in r["rule"])
    assert egress["pass"] is True


def test_validate_boh_breakroom():
    results = validate_constraints(VALID_ASSIGNMENTS)
    boh = next(r for r in results if "BOH-Breakroom" in r["rule"])
    assert boh["pass"] is True


# --- get_task_color ---

def test_task_color_mapping():
    assert get_task_color("Floor_2") == TASK_COLORS["Floor"]
    assert get_task_color("Outdoor - DP") == TASK_COLORS["Outdoor"]
    assert get_task_color("Break") == TASK_COLORS["Break"]
    assert get_task_color("Restroom_4") == TASK_COLORS["Restroom"]
    assert get_task_color("Egress") == TASK_COLORS["Egress"]
    assert get_task_color("BOH-Breakroom") == TASK_COLORS["BOH"]
    assert get_task_color("Float_0") == TASK_COLORS["Float"]

