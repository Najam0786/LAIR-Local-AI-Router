from app.memory.store import MemoryStore


def test_remember_creates_a_new_record(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    record = store.remember("project-a", "user prefers dark mode", [1.0, 0.0, 0.0])

    assert record.project_scope == "project-a"
    assert record.text == "user prefers dark mode"
    assert store.get(record.memory_id) is not None


def test_similar_memory_in_same_scope_updates_instead_of_duplicating(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    first = store.remember("project-a", "user's name is Sam", [1.0, 0.0, 0.0])
    second = store.remember("project-a", "user's name is actually Samuel", [0.999, 0.0, 0.0])

    assert second.memory_id == first.memory_id
    assert store.list_for_scope("project-a")[0].text == "user's name is actually Samuel"
    assert len(store.list_for_scope("project-a")) == 1


def test_dissimilar_memory_in_same_scope_creates_a_second_record(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    store.remember("project-a", "fact one", [1.0, 0.0, 0.0])
    store.remember("project-a", "unrelated fact two", [0.0, 1.0, 0.0])

    assert len(store.list_for_scope("project-a")) == 2


def test_similar_embeddings_in_different_scopes_never_merge(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    store.remember("project-a", "fact in project a", [1.0, 0.0, 0.0])
    store.remember("project-b", "fact in project b", [1.0, 0.0, 0.0])

    assert len(store.list_for_scope("project-a")) == 1
    assert len(store.list_for_scope("project-b")) == 1


def test_forget_removes_a_single_memory(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    record = store.remember("project-a", "fact", [1.0, 0.0, 0.0])

    assert store.forget(record.memory_id) is True
    assert store.get(record.memory_id) is None


def test_forget_unknown_memory_returns_false(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")

    assert store.forget("no-such-id") is False


def test_forget_all_wipes_only_the_given_scope(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "fact a", [1.0, 0.0, 0.0])
    store.remember("project-b", "fact b", [0.0, 1.0, 0.0])

    removed = store.forget_all("project-a")

    assert removed == 1
    assert store.list_for_scope("project-a") == []
    assert len(store.list_for_scope("project-b")) == 1


def test_export_scope_includes_embeddings(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "fact", [1.0, 0.0, 0.0])

    exported = store.export_scope("project-a")

    assert len(exported) == 1
    assert exported[0]["embedding"] == [1.0, 0.0, 0.0]


def test_memories_persist_across_store_instances(tmp_path):
    path = tmp_path / "memory.json"
    MemoryStore(path=path).remember("project-a", "fact", [1.0, 0.0, 0.0])

    reloaded = MemoryStore(path=path)

    assert len(reloaded.list_for_scope("project-a")) == 1
