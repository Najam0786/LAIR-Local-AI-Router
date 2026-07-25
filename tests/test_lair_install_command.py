from app.integrations.base import ClientInstaller
from lair.commands import install as install_command


class _FakeInstaller(ClientInstaller):
    name = "fake"

    def __init__(self, detected: bool):
        self._detected = detected
        self.install_calls: list[str] = []
        self.uninstall_calls = 0

    def detect(self) -> bool:
        return self._detected

    def install(self, base_url: str) -> str:
        self.install_calls.append(base_url)
        return f"fake: installed at {base_url}"

    def uninstall(self) -> str:
        self.uninstall_calls += 1
        return "fake: uninstalled"


def test_run_with_named_client_installs_only_that_client(monkeypatch, capsys):
    fake = _FakeInstaller(detected=True)
    monkeypatch.setattr(install_command, "get_installer", lambda name: fake)

    install_command.run(client="fake", base_url="http://x/v1")

    assert fake.install_calls == ["http://x/v1"]
    assert "installed at http://x/v1" in capsys.readouterr().out


def test_run_with_named_client_uninstalls_when_flagged(monkeypatch, capsys):
    fake = _FakeInstaller(detected=True)
    monkeypatch.setattr(install_command, "get_installer", lambda name: fake)

    install_command.run(client="fake", uninstall=True)

    assert fake.uninstall_calls == 1
    assert "uninstalled" in capsys.readouterr().out


def test_run_with_unknown_client_reports_planned_clients(capsys):
    install_command.run(client="cursor")

    out = capsys.readouterr().out
    assert "not yet auto-installable" in out


def test_run_with_unrecognized_client_lists_supported_and_planned(capsys):
    install_command.run(client="totally-unknown-client")

    out = capsys.readouterr().out
    assert "Unknown client" in out
    assert "continue" in out


def test_run_with_no_args_installs_into_all_detected_clients(monkeypatch, capsys):
    detected = _FakeInstaller(detected=True)
    not_detected = _FakeInstaller(detected=False)
    monkeypatch.setattr(
        install_command,
        "INSTALLERS",
        {"detected": detected, "not-detected": not_detected},
    )

    install_command.run(base_url="http://x/v1")

    assert detected.install_calls == ["http://x/v1"]
    assert not_detected.install_calls == []


def test_run_with_no_args_and_nothing_detected_reports_that(monkeypatch, capsys):
    not_detected = _FakeInstaller(detected=False)
    monkeypatch.setattr(install_command, "INSTALLERS", {"x": not_detected})

    install_command.run()

    out = capsys.readouterr().out
    assert "No supported clients detected" in out
