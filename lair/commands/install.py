from app.core.settings import settings
from app.integrations.registry import INSTALLERS, PLANNED_CLIENTS, get_installer


def default_base_url() -> str:
    return f"http://{settings.HOST}:{settings.PORT}/v1"


def run(
    client: str | None = None,
    uninstall: bool = False,
    base_url: str | None = None,
) -> None:
    """
    `python -m lair install [--client NAME] [--uninstall] [--base-url URL]`

    With no `--client`, detects which supported clients are present
    and installs into all of them (I-14) -- never auto-downloads or
    touches anything beyond each client's own config file.
    """

    base_url = base_url or default_base_url()

    if client is not None:
        installer = get_installer(client)

        if installer is None:
            _print_unknown_client(client)
            return

        print(installer.uninstall() if uninstall else installer.install(base_url))
        return

    detected = [
        installer for installer in INSTALLERS.values() if installer.detect()
    ]

    if not detected:
        print("No supported clients detected.")
        _print_planned_clients()
        return

    print(f"Detected {len(detected)} supported client(s):")
    for installer in detected:
        summary = installer.uninstall() if uninstall else installer.install(base_url)
        print(f"  {summary}")

    _print_planned_clients()


def _print_unknown_client(client: str) -> None:
    if client in PLANNED_CLIENTS:
        print(
            f"'{client}' is a known target but not yet auto-installable -- "
            "its config schema hasn't been verified stable enough to write "
            "automatically. Point it at LAIR manually: "
            f"{default_base_url()}"
        )
        return

    print(
        f"Unknown client '{client}'. Supported: {', '.join(INSTALLERS)}. "
        f"Planned: {', '.join(PLANNED_CLIENTS)}."
    )


def _print_planned_clients() -> None:
    print(
        f"\nPlanned but not yet auto-installable: {', '.join(PLANNED_CLIENTS)} "
        f"-- point them at LAIR manually if you use one: {default_base_url()}"
    )
