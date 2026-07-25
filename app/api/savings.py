from fastapi import APIRouter

from app.costs.ledger import default_savings_ledger
from app.schemas.savings import SavingsResponse

router = APIRouter(tags=["Savings"])


@router.get("/v1/lair/savings", response_model=SavingsResponse)
async def get_savings() -> SavingsResponse:
    """
    Running cloud-equivalent cost avoided by routing locally
    (day / month / lifetime totals).
    """

    totals = default_savings_ledger.totals()

    return SavingsResponse(**totals.model_dump())
