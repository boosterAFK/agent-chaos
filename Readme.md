# Agent Chaos Suite

> **A headless testing harness for evaluating trajectory resilience in multi-step agent graphs.**

---

## The Industry Gap

Most public benchmarks (like SWE-bench or basic QA benchmarks) only score the **final outcome**:

- Did the code compile?
- Did the string match?
- Was the execution completed?

In production, what kills an agent is its **trajectory**:

- Circular retry loops that burn $50 in API credits
- Hallucinated tool arguments
- Silent recovery failures
- Catastrophic latency degradation under tool timeouts

---

## What We Built

**Agent Chaos Suite** is a headless testing harness that subjects multi-step agent graphs (e.g., LangGraph, AutoGen) to synthetic failure modes to evaluate **trajectory resilience**.

---

## Target Environments & Fault Injection

We test on two natural occurrences of distributed agentic systems. Because protocols like MCP (Model Context Protocol) operate over the network, we systematically inject faults at two distinct layers **without needing to alter the agent's underlying source code**:

### HTTP-Level

Simulating realistic transport API failures such as:

- 504 timeouts
- Connection drops
- HTTP 429 rate limits

### Semantic-Level

Injecting malformed JSON responses, omission faults, and schema mutations into the agent's middleware to test its **cognitive resilience** and **hallucination risks**.

---

## What We Measure (Trajectory Health Metrics)

We compute concrete, quantitative scores to move beyond qualitative "vibe checks":

| Metric                            | Description                                                                                   |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| **Step Efficiency Ratio**         | `Optimal Steps / Actual Steps Taken`                                                          |
| **Self-Correction Recovery Rate** | The percentage of recovered states after encountering a tool error without human intervention |
| **Cost/Token Blast Radius**       | The cost variance and token bloat under degraded environmental states                         |

---

## What We Provide

### Automated Tracing

Export full span trees showing tool calls, retry loops, and state changes to observability backends like **Jaeger** or **Arize Phoenix** via **OpenTelemetry**.

### Enterprise API & Mocking Engine

An API to convert any existing project into a set of executable agents to run out-of-network. By adding annotations to your existing source code tests, you can convert internal tools into basic agents. This allows companies to target internal systems safely without world-facing exposure.

### Interactive UI

A dedicated dashboard to visualize execution parameters, manipulate fault injection strategies, and play with the telemetry data in real-time.

---

## Summary

Agent Chaos Suite moves agent evaluation beyond pass/fail outcomes and into the realm of **trajectory health**—measuring how agents behave when the network fails, the schema breaks, and the retries pile up.
