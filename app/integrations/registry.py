from app.integrations.base import ClientInstaller
from app.integrations.continue_client import ContinueInstaller

# Only clients with a verified, stable, file-based config surface get a
# real installer -- writing an unverified schema risks corrupting a
# config LAIR didn't create. `docs/DOGFOODING.md` (DF-005) already
# established Continue as the reliable client for real usage; the
# others named in docs/INNOVATION_PLAN_2026.md I-14 (Cline, Cursor,
# Windsurf, Zed) stay planned, not guessed at.
INSTALLERS: dict[str, ClientInstaller] = {
    "continue": ContinueInstaller(),
}

PLANNED_CLIENTS: list[str] = ["cline", "cursor", "windsurf", "zed"]


def get_installer(name: str) -> ClientInstaller | None:
    return INSTALLERS.get(name)
