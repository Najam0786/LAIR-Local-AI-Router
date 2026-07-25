import json

from app.memory.store import MemoryStore
from lair.commands import memory as memory_command


def test_list_memories_reports_none_for_empty_scope(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    output = memory_command.list_memories("project-a", store=store)

    assert "No memories" in output


def test_list_memories_shows_stored_text(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "prefers dark mode", [1.0, 0.0, 0.0])

    output = memory_command.list_memories("project-a", store=store)

    assert "prefers dark mode" in output


def test_show_memory_by_id(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    record = store.remember("project-a", "prefers dark mode", [1.0, 0.0, 0.0])

    output = memory_command.show_memory(record.memory_id, store=store)

    assert "prefers dark mode" in output
    assert record.memory_id in output


def test_show_unknown_memory(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    output = memory_command.show_memory("no-such-id", store=store)

    assert "No memory found" in output


def test_forget_memory_by_id(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    record = store.remember("project-a", "fact", [1.0, 0.0, 0.0])

    output = memory_command.forget_memory(record.memory_id, store=store)

    assert output == "Forgotten."
    assert store.get(record.memory_id) is None


def test_wipe_scope_removes_all_memories_in_scope(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "fact one", [1.0, 0.0, 0.0])
    store.remember("project-a", "unrelated fact", [0.0, 1.0, 0.0])

    output = memory_command.wipe_scope("project-a", store=store)

    assert "Removed 2" in output
    assert store.list_for_scope("project-a") == []


def test_export_scope_returns_valid_json(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "fact", [1.0, 0.0, 0.0])

    output = memory_command.export_scope("project-a", store=store)
    parsed = json.loads(output)

    assert len(parsed) == 1
    assert parsed[0]["text"] == "fact"
