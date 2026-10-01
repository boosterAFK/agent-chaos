# BlastRadius Eval Suite

> **A headless testing harness that measures how multi-step agents behave when their tools fail.**

Most benchmarks only score the final outcome - did it compile, did the string match. In production,
what kills an agent is its **trajectory**: circular retry loops burning API credits, silent recovery
failures, latency degradation under tool timeouts. BlastRadius Eval Suite subjects agent graphs to
deterministic, pre-computed fault schedules and scores the resulting trajectory.

---

## Quickstart

```bash
# 1. Install dependencies (uv manages the .venv at the repo root)
uv sync

# 2. Add your OpenAI key
cp .env.example .env   # then set OPENAI_API_KEY=...

# 3. Run the benchmark
.venv\Scripts\python.exe examples/run_benchmark.py
```

Expected output:

```
Efficiency: 0.5714285714285714
Recovery Rate: 1.0
Graceful Termination: 1.0
```

---

## How it works

```
examples/langgraph/            PURE WORKFLOW CATALOG (test subjects)
  minimal_llm_agent.py           -> TOOLS + build_workflow(tools) + PROMPT
        |                          no imports from injector/runner/frameworks
        v
examples/run_benchmark.py      SOLE WIRING POINT
        |
        |-- FrameworkProvider (Abstract Factory)
        |      -> make_runner() / make_evaluator() / make_tool_adapter()
        |      frameworks/langgraph/: LangGraphProvider
        |
        +-- FaultInjector (dispatcher, framework-agnostic)
               -> poison_tools()  clones tools via the adapter, swaps .func
               -> dispatch()      routes each observed call to the schedulers
                    |
                    +-- FaultScheduler (pluggable strategies, own their logic)
                    |      FixedCallScheduler  -> fire on call N  (at_calls=(1,2))
                    |      GraphFaultScheduler -> x2 call arms x1 (trigger_on="...")
                    |
                    +-- ChaosToolProxy -> becomes the tool\'s func; per-call fault
                                          decision means NO runtime graph mutation
```

### The pieces

| Component | Role |
| --- | --- |
| **Workflow catalog** (`examples/langgraph/`) | Pure test subjects. Each module exposes `TOOLS`, `build_workflow(tools)`, and `PROMPT`. They never import chaos code. |
| **FaultScheduler** (`injector/schedulers/`) | Pluggable strategies that decide WHEN a fault fires. Each owns its arming logic and state. |
| **FaultInjector** (`injector/base.py`) | Framework-agnostic dispatcher. Owns the scheduler set, enforces strict target ownership, produces poisoned tool clones. |
| **ChaosToolProxy** (`injector/chaos_tool_proxy.py`) | Generic callable wrapper installed as the tool\'s `func`; asks the injector on every call whether to fault. |
| **FrameworkProvider** (`frameworks/`) | Abstract Factory returning a matched family (runner + evaluator + tool adapter) for one framework. |
| **AgentRunner** (`runner/base.py`, `frameworks/langgraph/runner.py`) | Dumb executor. Receives a fully-built (already-poisoned) workflow; never touches tools or faults. |

---

## Writing your own scenario

```python
from frameworks.langgraph import LangGraphProvider
from examples.langgraph.minimal_llm_agent import PROMPT, TOOLS, build_workflow
from injector.base import FaultInjector
from injector.faults import TimeoutFault
from injector.schedulers import FixedCallScheduler
from langchain_core.messages import HumanMessage

framework = LangGraphProvider()

# 1. Arm a scheduling strategy (it owns its arming logic).
scheduler = FixedCallScheduler()
scheduler.register_fault("fetch_data", TimeoutFault(delay_seconds=0.1), at_calls=(1, 2))

# 2. Poison the tools (originals stay pristine) and build the workflow.
injector = FaultInjector(schedulers=[scheduler], adapter=framework.make_tool_adapter())
workflow = build_workflow(injector.poison_tools(TOOLS))

# 3. Run with a dumb executor and score the trajectory.
runner = framework.make_runner(uncompiled_graph=workflow)
runner.invoke({"messages": [HumanMessage(content=PROMPT)]}, thread_id="chaos-001", recursion_limit=100)
final_state = runner.get_state("chaos-001")

evaluator = framework.make_evaluator(optimal_steps=4)
print(evaluator.calculate_efficiency_ratio(final_state))
print(evaluator.calculate_recovery_rate(final_state))
print(evaluator.calculate_graceful_termination(final_state))
```

### Cross-tool triggers

`GraphFaultScheduler` expresses interaction logic across tools - e.g. "after
`report_unavailable` is called, the NEXT `fetch_data` call fails":

```python
from injector.schedulers import GraphFaultScheduler

graph = GraphFaultScheduler()
graph.register_fault("fetch_data", TimeoutFault(delay_seconds=0.1), trigger_on="report_unavailable")
```

Trigger tools are observed but never faulted; each trigger call arms the target, the fault fires once,
then the target recovers until re-armed.

---

## What we measure

| Metric | Description |
| --- | --- |
| **Step Efficiency Ratio** | `Optimal Steps / Actual Steps Taken` |
| **Self-Correction Recovery Rate** | Recovered states after a tool error, no human intervention |
| **Graceful Termination** | Whether the run ends via a designated terminal path rather than an error |
| **Cost/Token Blast Radius** | Cost variance and token bloat under degraded states (roadmap) |

---

## Design guarantees

- **Deterministic.** The same fault schedule always produces the same trajectory - reproducible
  benchmarks, not random chaos.
- **Clone-don\'t-mutate.** Poisoning clones tools (`model_copy` + `func` swap); originals stay
  pristine and reusable, and no graph is ever mutated at runtime.
- **Strict ownership.** Two schedulers cannot target the same tool; the injector raises on conflict.
- **Dumb runners.** Runners receive a finished workflow and cannot leak faults between runs.

---

## Project layout

```
injector/            chaos core: Fault, FaultInjector (dispatcher), ChaosToolProxy
  schedulers/          pluggable strategies: FixedCallScheduler, GraphFaultScheduler
  adapters/base.py     ToolAdapter ABC (framework-agnostic tool seam)
  faults/              TimeoutFault, RateLimitFault, MalformedJSONFault, SchemaMutationFault
frameworks/          Abstract Factory per framework
  base.py              FrameworkProvider ABC
  langgraph/           LangGraphProvider: runner + evaluator + tool adapter
runner/base.py       AgentRunner ABC (framework-agnostic executor)
telemetry/           MetricEvaluator ABC + instrumentation (OTel, stub)
examples/
  langgraph/           pure workflow catalog (TOOLS, build_workflow, PROMPT)
  run_benchmark.py     sole benchmark entry point
infrastructure/      docker-compose for Jaeger / otel-collector
```

---

## Roadmap

- OpenTelemetry span export to Jaeger / Arize Phoenix (instrumentation is currently a stub).
- HTTP-level fault injection at the MCP transport layer (504s, connection drops, 429s).
- Async tool support, richer scheduler conditions, fault-reactive schedulers.
- Enterprise API & mocking engine; interactive telemetry dashboard.
