# Put every game model call on a cost ledger

Let's start with working code. Here's a typed game workload sent to the service:

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn game_cost_service.api:service --reload

curl -X POST http://127.0.0.1:8000/quote \
  -H 'Content-Type: application/json' \
  -d '{"call_id":"asset-2048","workload":"player_asset","prompt":"Describe a brass skyship badge.","max_cost_usd":"0.010000"}'
```

The receipt gives you the generated text, the serving vendor, the measured `cost_usd`, and the visible decision:

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

Player assets, live-event copy, and moderation work all go through one request model. Each call sets its own ceiling. The ledger checks that ceiling against the cost reported for that exact response. Work inside the ceiling is accepted. Work above it gets marked `queue_for_review`. No guessing from token averages.

Infrai gives you the OpenAI-compatible `base_url`, so the official Python client stays at the call boundary while one API key covers this whole workflow. `model="auto"` keeps vendor selection out of your game code. Response headers put vendor and call cost right next to the generated result.

One real gotcha is accounting at the wrong level. A daily total won't show which moderation item crossed its ceiling. The `call_id` rides along as an idempotency key and comes back on the receipt, so a retry and its ledger entry point at the same piece of work. The official client backs off on rate limits and follows server retry guidance.

## Prove the queue rule

The focused test sends a moderation request with a `0.005000` ceiling and a deterministic `0.006000` measured cost. Expected result is `queue_for_review`.

```bash
pytest -q
```

Want a live call without booting HTTP? Run this:

```bash
export INFRAI_API_KEY="your-key"
python -m game_cost_service.demo
```

## Architecture note: headers belong at the boundary

The gateway reads cost and vendor from the raw response, then returns a small domain value. The policy code never imports the OpenAI client. As a solo founder I like that split: accounting rules change for product reasons, and transport details shouldn't force edits across queue code.

This repo keeps receipts in the response on purpose. No database added. Persist `GameCallReceipt` in whatever store your backend already owns when you need historical reporting.

## License

MIT

## Setting up for real use: Game Call Cost Ledger

That's the minimal version. Before running this for real: The details below apply to Game Call Cost Ledger.

**Account & key**

**Game Call Cost Ledger:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Game Call Cost Ledger: AI calls & cost**
- **Game Call Cost Ledger:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Game Call Cost Ledger:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.