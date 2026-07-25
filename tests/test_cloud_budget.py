from datetime import datetime, timedelta, timezone

from app.costs.budget import CloudBudgetLedger


def test_remaining_equals_full_budget_when_nothing_spent(tmp_path):
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    assert ledger.remaining_this_month() == 10.0


def test_record_reduces_remaining_budget(tmp_path):
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    ledger.record(3.5)

    assert ledger.spent_this_month() == 3.5
    assert ledger.remaining_this_month() == 6.5


def test_remaining_never_goes_negative(tmp_path):
    ledger = CloudBudgetLedger(monthly_budget_usd=5.0, path=tmp_path / "b.json")

    ledger.record(4.0)
    ledger.record(4.0)  # would be -3.0 without clamping

    assert ledger.remaining_this_month() == 0.0


def test_zero_budget_means_no_headroom(tmp_path):
    ledger = CloudBudgetLedger(monthly_budget_usd=0.0, path=tmp_path / "b.json")

    assert ledger.remaining_this_month() == 0.0


def test_only_current_months_spend_counts(tmp_path):
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")
    ledger.record(4.0)

    now = datetime.now(timezone.utc)
    last_month = now.replace(day=1) - timedelta(days=1)

    assert ledger.remaining_this_month(now=last_month) == 10.0


def test_persists_across_instances(tmp_path):
    path = tmp_path / "b.json"
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=path)
    ledger.record(2.0)

    reloaded = CloudBudgetLedger(monthly_budget_usd=10.0, path=path)

    assert reloaded.spent_this_month() == 2.0
