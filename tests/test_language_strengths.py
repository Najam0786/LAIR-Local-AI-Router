from app.registry.language_strengths import LanguageStrengthTable


def _write_table(tmp_path):
    path = tmp_path / "language_strengths.yaml"
    path.write_text(
        """
model_language_strengths:
  qwen:
    - en
    - es
    - zh-cn
  smollm:
    - en
""",
        encoding="utf-8",
    )
    return path


def test_supports_matches_declared_language(tmp_path):
    table = LanguageStrengthTable(path=_write_table(tmp_path))

    assert table.supports("qwen3-8b", "es") is True
    assert table.supports("qwen3-8b", "zh-cn") is True


def test_supports_false_for_undeclared_language(tmp_path):
    table = LanguageStrengthTable(path=_write_table(tmp_path))

    assert table.supports("smollm3-3b", "es") is False


def test_supports_false_for_unknown_model(tmp_path):
    table = LanguageStrengthTable(path=_write_table(tmp_path))

    assert table.supports("totally-unknown-model", "en") is False


def test_matching_is_case_insensitive(tmp_path):
    table = LanguageStrengthTable(path=_write_table(tmp_path))

    assert table.supports("QWEN3-8B", "ES") is True


def test_missing_file_yields_no_matches(tmp_path):
    table = LanguageStrengthTable(path=tmp_path / "missing.yaml")

    assert table.supports("qwen3-8b", "en") is False
