from fastapi import FastAPI

from .call_ledger import GameCallReceipt, GameCallRequest, record_game_call
from .infrai_gateway import InfraiGateway

service = FastAPI(title="Game Call Cost Ledger")


@service.post("/quote", response_model=GameCallReceipt)
def quote(request: GameCallRequest) -> GameCallReceipt:
    return record_game_call(request, InfraiGateway())
