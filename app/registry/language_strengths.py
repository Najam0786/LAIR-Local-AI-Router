from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "configs" / "language_strengths.yaml"


class LanguageStrengthTable:
    """
    Declared per-model language support (I-10), matched by model-id
    substring the same way `PricingTable` (I-01) matches cloud price
    classes -- a model-id-substring -> declared-attribute pattern this
    codebase already established, not a new one.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._entries: dict[str, set[str]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return

        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}

        self._entries = {
            pattern.lower(): {code.lower() for code in codes}
            for pattern, codes in (data.get("model_language_strengths") or {}).items()
        }

    def supports(self, model_id: str, language_code: str) -> bool:
        model_id_lower = model_id.lower()
        language_code_lower = language_code.lower()

        for pattern, codes in self._entries.items():
            if pattern in model_id_lower and language_code_lower in codes:
                return True

        return False


default_language_strength_table = LanguageStrengthTable()
