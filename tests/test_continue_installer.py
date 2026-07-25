import json

from app.integrations.continue_client import LAIR_ENTRY_TITLE, ContinueInstaller


def test_detect_false_when_config_dir_missing(tmp_path):
    installer = ContinueInstaller(config_dir=tmp_path / "missing")

    assert installer.detect() is False


def test_install_creates_config_from_nothing(tmp_path):
    config_dir = tmp_path / ".continue"
    installer = ContinueInstaller(config_dir=config_dir)

    installer.install("http://127.0.0.1:8000/v1")

    assert installer.detect() is True
    config = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    assert config["models"][0]["title"] == LAIR_ENTRY_TITLE
    assert config["models"][0]["apiBase"] == "http://127.0.0.1:8000/v1"


def test_install_preserves_existing_models_and_backs_up_original(tmp_path):
    config_dir = tmp_path / ".continue"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    original = {"models": [{"title": "My Other Model", "provider": "anthropic"}]}
    config_path.write_text(json.dumps(original), encoding="utf-8")

    installer = ContinueInstaller(config_dir=config_dir)
    installer.install("http://127.0.0.1:8000/v1")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    titles = [m["title"] for m in config["models"]]
    assert "My Other Model" in titles
    assert LAIR_ENTRY_TITLE in titles

    backup = json.loads(
        (config_dir / "config.json.lair-backup").read_text(encoding="utf-8")
    )
    assert backup == original


def test_reinstall_does_not_duplicate_the_lair_entry(tmp_path):
    installer = ContinueInstaller(config_dir=tmp_path / ".continue")

    installer.install("http://127.0.0.1:8000/v1")
    installer.install("http://127.0.0.1:9000/v1")

    config = json.loads(
        (tmp_path / ".continue" / "config.json").read_text(encoding="utf-8")
    )
    lair_entries = [m for m in config["models"] if m["title"] == LAIR_ENTRY_TITLE]
    assert len(lair_entries) == 1
    assert lair_entries[0]["apiBase"] == "http://127.0.0.1:9000/v1"


def test_uninstall_restores_real_original_config(tmp_path):
    config_dir = tmp_path / ".continue"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    original = {"models": [{"title": "My Other Model", "provider": "anthropic"}]}
    config_path.write_text(json.dumps(original), encoding="utf-8")

    installer = ContinueInstaller(config_dir=config_dir)
    installer.install("http://127.0.0.1:8000/v1")
    installer.uninstall()

    restored = json.loads(config_path.read_text(encoding="utf-8"))
    assert restored == original
    assert not (config_dir / "config.json.lair-backup").exists()


def test_uninstall_removes_file_lair_created_from_nothing(tmp_path):
    config_dir = tmp_path / ".continue"
    installer = ContinueInstaller(config_dir=config_dir)

    installer.install("http://127.0.0.1:8000/v1")
    installer.uninstall()

    assert not (config_dir / "config.json").exists()
    assert not (config_dir / "config.json.lair-created").exists()


def test_uninstall_with_no_backup_and_no_marker_is_a_safe_noop(tmp_path):
    installer = ContinueInstaller(config_dir=tmp_path / ".continue")

    result = installer.uninstall()

    assert "no backup found" in result.lower()


def test_repeated_install_never_overwrites_the_real_backup(tmp_path):
    config_dir = tmp_path / ".continue"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    original = {"models": [{"title": "My Other Model"}]}
    config_path.write_text(json.dumps(original), encoding="utf-8")

    installer = ContinueInstaller(config_dir=config_dir)
    installer.install("http://127.0.0.1:8000/v1")
    installer.install("http://127.0.0.1:9000/v1")
    installer.uninstall()

    restored = json.loads(config_path.read_text(encoding="utf-8"))
    assert restored == original
