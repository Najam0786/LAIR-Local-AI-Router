import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path
from threading import Lock

from pydantic import BaseModel

from app.core.settings import settings

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "logs" / "response_cache.json"


class CachedResponse(BaseModel):
    """
    A previously-served answer, keyed by the exact conversation that
    produced it.
    """

    text: str
    finish_reason: str | None = None
    completion_tokens: int | None = None
    prompt_tokens: int | None = None
    model_id: str
    cached_at: float


def cache_key_for(messages: list[dict]) -> str:
    """
    Exact-match cache key over the *entire* conversation -- role and
    content of every message, not just the latest prompt -- so a
    materially different conversation history never collides (I-07's
    "never cache when conversation history differs materially").
    """

    normalized = json.dumps(
        [
            {"role": message.get("role"), "content": message.get("content")}
            for message in messages
        ],
        sort_keys=True,
    )

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ResponseCache:
    """
    Exact-match response cache (I-07, Phase 1).

    Serves a prior answer at zero token/GPU cost when a request's full
    conversation matches a past one exactly. Embedding-based near-match
    similarity is explicitly Phase 2, not built here -- I-07's own
    design notes sequence "exact-match tier first," and the shared
    embedding layer I-08/I-18 are meant to reuse doesn't exist yet.

    In-memory `OrderedDict` for O(1) get/put and LRU eviction, with the
    same JSON-backed persistence pattern `KnowledgeBase`/
    `DecisionRepository`/`SavingsLedger` already use -- no new storage
    mechanism introduced for this feature.
    """

    def __init__(
        self,
        max_entries: int | None = None,
        ttl_seconds: int | None = None,
        path: Path | str = _DEFAULT_PATH,
    ):
        self._max_entries = (
            max_entries
            if max_entries is not None
            else settings.RESPONSE_CACHE_MAX_ENTRIES
        )
        self._ttl_seconds = (
            ttl_seconds
            if ttl_seconds is not None
            else settings.RESPONSE_CACHE_TTL_SECONDS
        )
        self._path = Path(path)
        self._lock = Lock()
        self._entries: OrderedDict[str, CachedResponse] = OrderedDict()
        self._load()

    def get(self, key: str) -> CachedResponse | None:
        with self._lock:
            entry = self._entries.get(key)

            if entry is None:
                return None

            if time.time() - entry.cached_at > self._ttl_seconds:
                del self._entries[key]
                return None

            self._entries.move_to_end(key)
            return entry

    def put(self, key: str, response: CachedResponse) -> None:
        with self._lock:
            self._entries[key] = response
            self._entries.move_to_end(key)

            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

            self._save()

    def _load(self) -> None:
        if not self._path.exists():
            return

        text = self._path.read_text(encoding="utf-8").strip()

        if not text:
            return

        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            return

        for key, value in raw.items():
            try:
                self._entries[key] = CachedResponse(**value)
            except Exception:
                continue

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                {
                    key: json.loads(entry.model_dump_json())
                    for key, entry in self._entries.items()
                },
                indent=2,
            ),
            encoding="utf-8",
        )


default_response_cache = ResponseCache()
