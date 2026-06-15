# Rogue Resilience — Roadmap

Delivery status for the official Rogue Resilience extension. See [PLAN.md](./PLAN.md) for full architecture.

## Phase 1 — Foundation ✅

- [x] `rogue/injectors/` — 5 built-in strategies + registry
- [x] `rogue/resilience/models.py` + architecture catalog
- [x] `ResilienceOrchestrator` single-agent Python protocol
- [x] Core metrics: detection, containment, recovery
- [x] `ResilienceJob` SDK types + REST API + job persistence
- [x] Unit tests for injectors + metrics
- [x] `docs/resilience/README.md`

## Phase 2 — Multi-Agent & Checkpoints ✅

- [x] Architecture profiles (hierarchical, peer-to-peer, supervisor-worker)
- [x] `MultiAgentPythonClient` with `agent_id` routing
- [x] LangGraph checkpoint adapter (`MemorySaver` / optional)
- [x] Cascading failure + system degradation metrics
- [x] Examples: hierarchical + LangGraph recovery demos
- [x] Integration tests with mocked multi-agent entrypoints

## Phase 3 — Dashboard & Reporting ✅

- [x] Web routes `/resilience/*` (list, configure, live, report)
- [x] Live trace viewer + agent graph + metrics radar
- [x] Resilience report generator (markdown / CSV / web JSON)
- [x] WebSocket `resilience_trace_update` events
- [x] CLI `--evaluation-mode resilience`
- [x] Dashboard sidebar + operational console cards
- [x] CI resilience test job in `test.yml`

## Phase 4 — Advanced & Polish ✅

- [x] Custom injector plugin API (`load_injector_plugin`, `register_injector`)
- [x] Concurrent multi-injection (`concurrent_target_agent_ids`)
- [x] Premium injector catalog + local `gradual_goal_drift` strategy
- [x] Deckard premium metadata (`deckard_adaptive_injection` stub in catalog)
- [x] TUI resilience catalog screen (`packages/tui/internal/screens/resilience/`)
- [x] CI regression gate workflow (`resilience-gate.yml`)
- [x] Auto-generated experiment templates (`POST /api/v1/resilience/scenarios/generate`)
- [x] Optional job score gate (`min_resilience_score` in config)
- [x] Example custom plugin (`examples/custom_injector_plugin/`)
- [x] `docs/resilience/INJECTORS.md`

## Future (post Phase 4)

| Item | Notes |
|------|-------|
| Full TUI job runner | Mirror red-team submit + report from terminal |
| Deckard-hosted probe fetch | Live adaptive injections via Rogue Security API |
| CrewAI / AutoGen adapters | Generic checkpoint + protocol layer |
| Human-in-the-loop validation | Dashboard review queue for high-stakes runs |
| Public resilience leaderboard | Normalized scores across architectures |
| Red Team → Resilience synergy | Promote successful attacks to injector probes |

## Open questions

See [PLAN.md §12](./PLAN.md#12-open-questions-for-next-iteration) for guard-agent assumptions, sandboxing defaults, metric calibration, and benchmark standardization.

## Recommended next steps

1. **Open a PR** to [qualifire-dev/rogue](https://github.com/qualifire-dev/rogue) from `feature/rogue-resilience` with Phase 1–4 summary and test plan.
2. **Capture UI screenshots** per `docs/resilience/README.md` and attach to the PR.
3. **Run the resilience gate locally** before merge: `uv run pytest rogue/tests/test_*resilience* -v`
4. **Dogfood** hierarchical + LangGraph examples against real multi-agent stacks.
5. **Decide premium injector split** with Rogue Security (local vs Deckard-hosted).
