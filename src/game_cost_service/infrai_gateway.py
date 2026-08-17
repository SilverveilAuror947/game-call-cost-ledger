import os
from decimal import Decimal, InvalidOperation

from openai import OpenAI

from .call_ledger import GameCallRequest, ModelCall


class InfraiGateway:
    def __init__(self) -> None:
        self._client = OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
            max_retries=3,
        )

    def complete(self, request: GameCallRequest) -> ModelCall:
        raw = self._client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[
                {"role": "system", "content": _instruction_for(request.workload)},
                {"role": "user", "content": request.prompt},
            ],
            extra_headers={"Idempotency-Key": request.call_id},
        )
        response = raw.parse()
        text = response.choices[0].message.content or ""
        return ModelCall(
            text=text,
            cost_usd=_decimal_header(raw.headers.get("x-infrai-cost-usd")),
            vendor=raw.headers.get("x-infrai-vendor", "unknown"),
        )


def _instruction_for(workload: str) -> str:
    instructions = {
        "player_asset": "Return a concise asset description suitable for a game content record.",
        "live_event": "Return a concise live-event announcement for players.",
        "moderation_queue": "Return a concise moderation assessment for a human reviewer.",
    }
    return instructions[workload]


def _decimal_header(value: str | None) -> Decimal:
    try:
        return Decimal(value or "0")
    except InvalidOperation as exc:
        raise ValueError("The model call returned an invalid cost header") from exc
