"""Tests for narrative state replay pure function."""

import pytest
from domain.novel.services.narrative_state_replay import replay_entity_state


def test_replay_add_and_remove():
    """Test that add action overwrites attributes and remove action deletes them."""
    base = {"魔法": "水系"}
    events = [
        {"mutations": [{"attribute": "魔法", "action": "add", "value": "火系"}]},
        {
            "mutations": [
                {"attribute": "临时", "action": "add", "value": "x"},
                {"attribute": "临时", "action": "remove", "value": ""},
            ]
        },
    ]
    state = replay_entity_state(base, events)
    assert state["魔法"] == "火系"
    assert "临时" not in state


def test_replay_empty_events():
    """Test that empty events list returns a copy of base attributes."""
    base = {"魔法": "水系", "等级": "5"}
    events = []
    state = replay_entity_state(base, events)

    # Should return a copy with same content
    assert state == base
    # Should be a different object (not mutating original)
    assert state is not base


def test_replay_unknown_action():
    """Test that unknown actions are ignored (with debug logging)."""
    base = {"魔法": "水系"}
    events = [
        {"mutations": [{"attribute": "魔法", "action": "unknown", "value": "火系"}]},
        {"mutations": [{"attribute": "等级", "action": "add", "value": "10"}]},
    ]
    state = replay_entity_state(base, events)

    # Unknown action should be ignored, base value preserved
    assert state["魔法"] == "水系"
    # Valid add action should work
    assert state["等级"] == "10"


def test_replay_multiple_mutations_in_single_event():
    """Test that multiple mutations in a single event are applied in order."""
    base = {"a": "1"}
    events = [
        {
            "mutations": [
                {"attribute": "b", "action": "add", "value": "2"},
                {"attribute": "c", "action": "add", "value": "3"},
                {"attribute": "a", "action": "remove", "value": ""},
            ]
        }
    ]
    state = replay_entity_state(base, events)

    assert "a" not in state
    assert state["b"] == "2"
    assert state["c"] == "3"


def test_replay_remove_nonexistent_attribute():
    """Test that removing a non-existent attribute doesn't cause errors."""
    base = {"魔法": "水系"}
    events = [
        {"mutations": [{"attribute": "不存在", "action": "remove", "value": ""}]}
    ]
    state = replay_entity_state(base, events)

    # Should not raise error, base preserved
    assert state == base


def test_replay_preserves_base_immutability():
    """Test that the base dictionary is not modified during replay."""
    base = {"魔法": "水系"}
    original_base = base.copy()
    events = [
        {"mutations": [{"attribute": "魔法", "action": "add", "value": "火系"}]}
    ]

    state = replay_entity_state(base, events)

    # Base should remain unchanged
    assert base == original_base
    # State should have the mutation applied
    assert state["魔法"] == "火系"
