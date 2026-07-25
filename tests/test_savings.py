from app.costs.calculator import CostCalculator
from app.costs.ledger import SavingsLedger
from app.costs.pricing import PricingTable


def _write_pricing(tmp_path):
    path = tmp_path / "cloud_pricing.yaml"
    path.write_text(
        """
classes:
  gpt4_class:
    input_per_1m_usd: 5.00
    output_per_1m_usd: 15.00
  budget_class:
    input_per_1m_usd: 0.15
    output_per_1m_usd: 0.60

model_classes:
  deepseek-r1-distill-qwen-32b: gpt4_class
""",
        encoding="utf-8",
    )
    return path


def test_explicit_mapping_takes_priority(tmp_path):
    table = PricingTable(path=_write_pricing(tmp_path))

    assert table.class_for_model("deepseek-r1-distill-qwen-32b") == "gpt4_class"


def test_size_heuristic_fallback_for_unmapped_model(tmp_path):
    table = PricingTable(path=_write_pricing(tmp_path))

    # Not in model_classes, but "3b" implies budget_class via the fallback.
    assert table.class_for_model("smollm3-3b") == "budget_class"


def test_unparseable_model_id_has_no_price_class(tmp_path):
    table = PricingTable(path=_write_pricing(tmp_path))

    assert table.class_for_model("some-custom-model") is None


def test_cost_calculator_three_pricing_scenarios(tmp_path):
    table = PricingTable(path=_write_pricing(tmp_path))
    calculator = CostCalculator(pricing_table=table)

    # Scenario 1: explicit mapping, real token counts.
    savings = calculator.estimate_savings_usd(
        "deepseek-r1-distill-qwen-32b", prompt_tokens=1_000_000, completion_tokens=0
    )
    assert savings == 5.00

    # Scenario 2: heuristic fallback mapping.
    savings = calculator.estimate_savings_usd(
        "smollm3-3b", prompt_tokens=0, completion_tokens=1_000_000
    )
    assert savings == 0.60

    # Scenario 3: unmapped model -- savings must be null, never guessed.
    savings = calculator.estimate_savings_usd(
        "unknown-model", prompt_tokens=1_000, completion_tokens=1_000
    )
    assert savings is None


def test_ledger_totals_aggregate_day_month_lifetime(tmp_path):
    ledger = SavingsLedger(path=tmp_path / "savings.json")

    ledger.record("model-a", 1.5)
    ledger.record("model-b", 2.5)

    totals = ledger.totals()

    assert totals.day_usd == 4.0
    assert totals.month_usd == 4.0
    assert totals.lifetime_usd == 4.0


def test_ledger_totals_empty_store_is_zero(tmp_path):
    ledger = SavingsLedger(path=tmp_path / "missing.json")

    totals = ledger.totals()

    assert totals.day_usd == 0.0
    assert totals.month_usd == 0.0
    assert totals.lifetime_usd == 0.0


def test_savings_endpoint_returns_totals(client):
    response = client.get("/v1/lair/savings")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"day_usd", "month_usd", "lifetime_usd"}


def test_chat_completion_response_includes_lair_meta(client, registered_fake_provider):
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "please debug this python function"}]},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["lair_meta"]["model_used"] == "qwen2.5-coder-32b"
    # qwen2.5-coder-32b resolves via the size heuristic (32b -> gpt4_class).
    assert body["lair_meta"]["estimated_savings_usd"] is not None


def test_chat_completion_updates_savings_ledger(client, registered_fake_provider):
    before = client.get("/v1/lair/savings").json()["lifetime_usd"]

    client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "please debug this python function"}]},
    )

    after = client.get("/v1/lair/savings").json()["lifetime_usd"]

    assert after > before
