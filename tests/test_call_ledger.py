from decimal import Decimal

from game_cost_service.call_ledger import GameCallRequest, ModelCall, record_game_call


class FixedGateway:
    def __init__(self, cost_usd: str) -> None:
        self.cost_usd = Decimal(cost_usd)

    def complete(self, request: GameCallRequest) -> ModelCall:
        return ModelCall("review result", self.cost_usd, "test-vendor")


def test_moderation_call_over_its_budget_enters_review_queue() -> None:
    request = GameCallRequest(
        call_id="moderation-1842",
        workload="moderation_queue",
        prompt="Assess player chat transcript 1842.",
        max_cost_usd=Decimal("0.005000"),
    )

    receipt = record_game_call(request, FixedGateway("0.006000"))

    assert receipt.decision == "queue_for_review"
    assert receipt.cost_usd == Decimal("0.006000")
    assert receipt.call_id == "moderation-1842"
