import json
from pathlib import Path

from app.integrations.base import ClientInstaller

LAIR_ENTRY_TITLE = "LAIR (Auto-routed)"


class ContinueInstaller(ClientInstaller):
    """
    Writes LAIR's OpenAI-compatible endpoint into Continue's
    `~/.continue/config.json` `models` array.

    Continue is the client `docs/DOGFOODING.md` (DF-005) established
    as the reliable one for real usage, and the exact
    "LAIR (Auto-routed)" title this writer uses already matches what
    was manually configured and verified end-to-end there.
    """

    name = "continue"

    def __init__(self, config_dir: Path | None = None):
        self._config_dir = config_dir or (Path.home() / ".continue")
        self._config_path = self._config_dir / "config.json"
        self._backup_path = self._config_dir / "config.json.lair-backup"
        # Marks that LAIR created config.json from nothing, so
        # uninstall() removes it instead of "restoring" content that
        # was never the user's original -- see uninstall()'s docstring.
        self._created_marker = self._config_dir / "config.json.lair-created"

    def detect(self) -> bool:
        return self._config_dir.exists()

    def install(self, base_url: str) -> str:
        if self._config_path.exists():
            if not self._backup_path.exists() and not self._created_marker.exists():
                self._backup_path.write_text(
                    self._config_path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            config = json.loads(self._config_path.read_text(encoding="utf-8"))
        else:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            if not self._backup_path.exists():
                self._created_marker.write_text("", encoding="utf-8")
            config = {}

        models = config.setdefault("models", [])
        models[:] = [m for m in models if m.get("title") != LAIR_ENTRY_TITLE]
        models.append(
            {
                "title": LAIR_ENTRY_TITLE,
                "provider": "openai",
                "model": "lair-auto",
                "apiBase": base_url,
                "apiKey": "not-needed",
            }
        )

        self._config_path.write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )

        return f'Continue: wrote "{LAIR_ENTRY_TITLE}" to {self._config_path}'

    def uninstall(self) -> str:
        """
        Restores config.json from the pre-install backup -- or, if
        LAIR created config.json from nothing (no prior file existed),
        removes it entirely rather than fabricating a "restore" of
        content that was never the user's.
        """

        if self._created_marker.exists():
            if self._config_path.exists():
                self._config_path.unlink()
            self._created_marker.unlink()

            return (
                f"Continue: removed {self._config_path} "
                "(LAIR created it; no prior config existed)."
            )

        if not self._backup_path.exists():
            return "Continue: no backup found -- nothing to restore."

        self._config_path.write_text(
            self._backup_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self._backup_path.unlink()

        return f"Continue: restored {self._config_path} from backup."
