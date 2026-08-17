from dataclasses import asdict, dataclass
from decimal import Decimal
import json
from typing import Literal, Protocol

Workload = Literal["player_asset", "live_event", "moderation_queue"]
Decision = Literal["accept", "queue_for_review"]

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
    BaseModel = None


if BaseModel is not None:
    class GameCallRequest(BaseModel):
        call_id: str = Field(min_length=1, max_length=80)
        workload: Workload
        prompt: str = Field(min_length=1, max_length=4_000)
        max_cost_usd: Decimal = Field(gt=0, decimal_places=6)


    class GameCallReceipt(BaseModel):
        call_id: str
        workload: Workload
        model_output: str
        cost_usd: Decimal
        vendor: str
        decision: Decision
else:
    @dataclass(frozen=True)
    class GameCallRequest:
        call_id: str
        workload: Workload
        prompt: str
        max_cost_usd: Decimal

        def __post_init__(self) -> None:
            if not 1 <= len(self.call_id) <= 80:
                raise ValueError("call_id must contain between 1 and 80 characters")
            if self.workload not in ("player_asset", "live_event", "moderation_queue"):
                raise ValueError("invalid workload")
            if not 1 <= len(self.prompt) <= 4_000:
                raise ValueError("prompt must contain between 1 and 4000 characters")
            if self.max_cost_usd <= 0 or self.max_cost_usd.as_tuple().exponent < -6:
                raise ValueError("max_cost_usd must be positive with at most 6 decimal places")


    @dataclass(frozen=True)
    class GameCallReceipt:
        call_id: str
        workload: Workload
        model_output: str
        cost_usd: Decimal
        vendor: str
        decision: Decision

        def model_dump_json(self, *, indent: int | None = None) -> str:
            return json.dumps(asdict(self), default=str, indent=indent)


@dataclass(frozen=True)
class ModelCall:
    text: str
    cost_usd: Decimal
    vendor: str


class ModelGateway(Protocol):
    def complete(self, request: GameCallRequest) -> ModelCall:
        """Return the measured result for one model call."""


def record_game_call(request: GameCallRequest, gateway: ModelGateway) -> GameCallReceipt:
    call = gateway.complete(request)
    decision: Decision = "accept" if call.cost_usd <= request.max_cost_usd else "queue_for_review"
    return GameCallReceipt(
        call_id=request.call_id,
        workload=request.workload,
        model_output=call.text,
        cost_usd=call.cost_usd,
        vendor=call.vendor,
        decision=decision,
    )
