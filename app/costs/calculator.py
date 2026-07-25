from app.costs.pricing import PricingTable, default_pricing_table


class CostCalculator:
    """
    Estimates the cloud-equivalent USD cost avoided by answering a
    request locally, using a model's mapped cloud price class.
    """

    def __init__(self, pricing_table: PricingTable | None = None):
        self._pricing_table = pricing_table or default_pricing_table

    def estimate_savings_usd(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float | None:
        price = self._pricing_table.price_for(model_id)

        if price is None:
            return None

        cost = (
            prompt_tokens / 1_000_000 * price.input_per_1m_usd
            + completion_tokens / 1_000_000 * price.output_per_1m_usd
        )

        return round(cost, 6)


default_cost_calculator = CostCalculator()
