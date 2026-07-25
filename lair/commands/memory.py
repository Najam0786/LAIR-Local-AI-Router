import json

from app.memory.store import MemoryStore, default_memory_store


def list_memories(project_scope: str, store: MemoryStore = default_memory_store) -> str:
    records = store.list_for_scope(project_scope)

    if not records:
        return f"No memories stored for project scope '{project_scope}'."

    lines = [f"Memories for '{project_scope}':", ""]
    for record in records:
        lines.append(f"  {record.memory_id}  ({record.updated_at.isoformat()})")
        lines.append(f"    {record.text}")

    return "\n".join(lines)


def show_memory(memory_id: str, store: MemoryStore = default_memory_store) -> str:
    record = store.get(memory_id)

    if record is None:
        return f"No memory found with id '{memory_id}'."

    return (
        f"memory_id:     {record.memory_id}\n"
        f"project_scope: {record.project_scope}\n"
        f"text:          {record.text}\n"
        f"created_at:    {record.created_at.isoformat()}\n"
        f"updated_at:    {record.updated_at.isoformat()}"
    )


def forget_memory(memory_id: str, store: MemoryStore = default_memory_store) -> str:
    removed = store.forget(memory_id)
    return "Forgotten." if removed else f"No memory found with id '{memory_id}'."


def wipe_scope(project_scope: str, store: MemoryStore = default_memory_store) -> str:
    removed_count = store.forget_all(project_scope)
    return f"Removed {removed_count} memory(ies) for scope '{project_scope}'."


def export_scope(project_scope: str, store: MemoryStore = default_memory_store) -> str:
    return json.dumps(store.export_scope(project_scope), indent=2)
