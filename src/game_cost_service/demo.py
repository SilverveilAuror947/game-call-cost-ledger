from decimal import Decimal

from .call_ledger import GameCallRequest, record_game_call
from .infrai_gateway import InfraiGateway


def main() -> None:
    receipt = record_game_call(
        GameCallRequest(
            call_id="event-summer-2026-copy-01",
            workload="live_event",
            prompt="Announce a double-XP weekend in one sentence.",
            max_cost_usd=Decimal("0.010000"),
        ),
        InfraiGateway(),
    )
    print(receipt.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
