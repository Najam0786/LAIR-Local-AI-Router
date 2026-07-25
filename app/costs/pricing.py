import re
from pathlib import Path

import yaml
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "configs" / "cloud_pricing.yaml"

_SIZE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)b(?![a-z0-9])")


class CloudPriceClass(BaseModel):
    """
    Per-1M-token USD pricing for a representative cloud tier.
    """

    input_per_1m_usd: float
    output_per_1m_usd: float


class PricingTable:
    """
    Maps local model ids to a cloud-equivalent price class.

    Explicit `model_classes` entries (substring match) take priority;
    unmatched models fall back to a parameter-count heuristic parsed from
    the model id. A model that matches neither has no price class --
    callers must treat that as "savings unknown", not zero.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._classes: dict[str, CloudPriceClass] = {}
        self._model_classes: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return

        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}

        self._classes = {
            name: CloudPriceClass(**fields)
            for name, fields in (data.get("classes") or {}).items()
        }
        self._model_classes = {
            pattern.lower(): class_name
            for pattern, class_name in (data.get("model_classes") or {}).items()
        }

    def class_for_model(self, model_id: str) -> str | None:
        model_id_lower = model_id.lower()

        for pattern, class_name in self._model_classes.items():
            if pattern in model_id_lower:
                return class_name

        return self._infer_class_from_size(model_id_lower)

    def _infer_class_from_size(self, model_id_lower: str) -> str | None:
        match = _SIZE_PATTERN.search(model_id_lower)

        if not match:
            return None

        params_b = float(match.group(1))

        if params_b >= 20:
            return "gpt4_class"
        if params_b >= 7:
            return "claude_class"
        return "budget_class"

    def price_for(self, model_id: str) -> CloudPriceClass | None:
        class_name = self.class_for_model(model_id)

        if class_name is None:
            return None

        return self._classes.get(class_name)


default_pricing_table = PricingTable()
