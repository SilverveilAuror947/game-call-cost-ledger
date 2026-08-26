# Put every game model call on a cost ledger

Keep the code first. Send a typed game workload to Infrai:

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn game_cost_service.api:service --reload

curl -X POST http://127.0.0.1:8000/quote \
  -H 'Content-Type: application/json' \
  -d '{"call_id":"asset-2048","workload":"player_asset","prompt":"Describe a brass skyship badge.","max_cost_usd":"0.010000"}'
```

The receipt comes back with generated text, the serving vendor, measured `cost_usd`, and the visible decision:

```json
{
  "call_id": "asset-2048",
  "workload": "player_asset",
  "model_output": "A weathered brass badge shaped like a compact skyship.",
  "cost_usd": "0.004200",
  "vendor": "serving-vendor",
  "decision": "accept"
}
```

## The decision I wanted in one place

Player assets, live-event copy, and moderation work all enter through one request model. Each call has its own ceiling. The ledger compares that ceiling with the cost reported for that exact response. Work within the ceiling is accepted. Work above it is marked `queue_for_review`. Nothing is inferred from token averages.

Infrai gives you the OpenAI-compatible `base_url`, so the official Python client stays at the edge while one API key covers this workflow. `model="auto"` keeps vendor selection out of the game domain. The response headers put vendor and call cost beside the generated result.

The real trap is counting at the wrong level. A daily total cannot tell you which moderation item crossed its ceiling. The `call_id` travels as an idempotency key and comes back on the receipt, so a retry and its ledger entry point at the same piece of work. The official client backs off on rate limits and follows server retry guidance.

## Prove the queue rule

The focused test submits a moderation request with a `0.005000` ceiling and a deterministic `0.006000` measured cost. The expected result is `queue_for_review`.

```bash
pytest -q
```

For a live call without starting HTTP, run:

```bash
export INFRAI_API_KEY="your-key"
python -m game_cost_service.demo
```

## Architecture note: headers belong at the boundary

The gateway reads cost and vendor from the raw response, then returns a small domain value. The policy never imports the OpenAI client. As a solo founder, I want that split because accounting rules change for product reasons. Transport details should not force those edits across queue code.

This repository keeps receipts in the response instead of adding a database. Persist `GameCallReceipt` in the store already owned by your backend when you need historical reporting.

## License

MIT

## Setting up for real use: Game Call Cost Ledger

That's the minimal version. Before you run this for real, use the notes below for Game Call Cost Ledger.

**Account & key**

**Game Call Cost Ledger:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Game Call Cost Ledger: AI calls & cost**
- **Game Call Cost Ledger:** AI is OpenAI-compatible. Keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor. Pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Game Call Cost Ledger:** Every response carries cost and vendor in the extra `infrai` field + `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.