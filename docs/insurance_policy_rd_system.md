# Insurance Policy R&D System

## Table of Contents

1. [Overview](#overview)
2. [System Goals](#system-goals)
3. [Platform Compatibility](#platform-compatibility) **← READ THIS FIRST IF ON WINDOWS**
4. [Architecture](#architecture)
5. [Technology Stack](#technology-stack)
6. [Microsoft Agent Framework (MAF)](#microsoft-agent-framework-maf)
7. [CodeAct — How It Works](#codeact--how-it-works)
8. [Why CodeAct vs Traditional Tool-Calling](#why-codeact-vs-traditional-tool-calling)
9. [Project Structure](#project-structure)
10. [Component Details](#component-details)
    - [Database Layer](#database-layer)
    - [Tools](#tools)
    - [Middleware](#middleware)
    - [Agent (main.py)](#agent-mainpy)
11. [Data Model](#data-model)
    - [Policy Document](#policy-document)
    - [Product / Add-on Document](#product--add-on-document)
12. [Seeded Demo Data](#seeded-demo-data)
    - [Policies](#policies)
    - [Products & Add-ons](#products--add-ons)
13. [Agent Flow — Step by Step](#agent-flow--step-by-step)
14. [Middleware Pipeline](#middleware-pipeline)
15. [Gemini LLM Integration](#gemini-llm-integration)
16. [Environment Variables](#environment-variables)
17. [Setup & Running](#setup--running)
18. [Testing](#testing)
19. [Expected Output](#expected-output)
20. [Extending the System](#extending-the-system)
21. [Design Decisions](#design-decisions)

---

## Overview

The **Insurance Policy R&D System** is a production-ready demo that demonstrates how to build an AI-powered upsell recommendation engine for insurance products using:

- **Microsoft Agent Framework (MAF)** for agent orchestration and middleware
- **CodeAct via `HyperlightCodeActProvider`** to collapse multi-tool workflows into a single sandboxed code execution turn
- **Google Gemini** as the LLM, wired through MAF's `client=` parameter (not via raw Gemini SDK)
- **mongomock** as a local MongoDB-compliant in-memory document store that works on both Windows and Linux without any server installation

---

## System Goals

Given a **policy number**, the system:

1. Retrieves the full policy record from the local document store
2. Fetches all available add-on products eligible for that policy type
3. Identifies gaps — features the policyholder does **not** currently have
4. Recommends the **top 3 best add-ons** to upsell, with:
   - Value explanation for the customer
   - Monthly cost of each add-on
   - Projected new premium
   - Estimated annual revenue increase for the insurer

---

## Platform Compatibility

### ⚠️ CRITICAL: Windows Users — READ THIS FIRST

This project uses **Hyperlight** for sandboxed code execution (CodeAct). Hyperlight requires hardware virtualization, which has **vastly different support** across platforms:

#### Platform Support Matrix

| Platform | Status | Details | Setup Required |
|---|---|---|---|
| **macOS (Intel & Apple Silicon)** | ✅ **Full Support** | Works out of the box | None — just install & run |
| **Linux with KVM** | ✅ **Full Support** | Requires KVM kernel module | [Setup Guide](./hyperlight-wsl2-kvm-setup.md) → sections 5-7 |
| **Windows 11 + WSL2** | ✅ **Full Support (Recommended)** | Requires nested virtualization + WSL2 kernel 6.x+ | **[MANDATORY: Complete this guide first](./hyperlight-wsl2-kvm-setup.md)** |
| **Windows 10 + WSL2** | ⚠️ **Unreliable** | Nested virtualization support is flaky | Not recommended; use WSL2 on Windows 11 instead |
| **Native Windows (no WSL)** | ❌ **Known to Fail** | Windows Hypervisor Platform (WHP) has numerous bugs | **DO NOT USE — switch to WSL2 instead** |

#### What This Means

- **If you are on macOS or Linux:** Just install dependencies and run. No special setup needed.
- **If you are on Windows 11:** You **MUST** use WSL2 and follow [the Hyperlight/WSL2 Setup Guide](./hyperlight-wsl2-kvm-setup.md) **before** trying to run this project. This is not optional.
- **If you are on Windows 10:** Nested virtualization in WSL2 is unreliable. Consider upgrading to Windows 11 or using a Linux VM instead.
- **If you are running native Windows (outside WSL):** Do not attempt to use this project. Hyperlight on native Windows has widespread failures due to WHP bugs. Your only option is to switch to WSL2 on Windows 11.

#### Common Native Windows Failures

If you run `python main.py` on native Windows, you will likely encounter:

```
Failed to create sandbox: failed to build ProtoWasmSandbox: No Hypervisor was found for Sandbox
```

or

```
hyperlight.HyperlightError: Cannot create sandbox runtime
```

**These errors cannot be fixed on native Windows.** The solution is to use **WSL2 on Windows 11** instead.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (CLI)                        │
│                                                             │
│   Agent(client=GeminiChatClient(),                          │
│          context_providers=[HyperlightCodeActProvider],      │
│          middleware=[log_tool_calls])                        │
└────────────────────────┬────────────────────────────────────┘
                         │  agent.run(query)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               HyperlightCodeActProvider                     │
│  (ContextProvider — injects execute_code tool + instructions)│
│                                                             │
│  Model generates ONE Python block:                          │
│    policy = call_tool("get_policy_details", ...)            │
│    offers = call_tool("get_current_offers", ...)            │
│    # analyse gaps ...                                       │
│                                                             │
│  Hyperlight sandbox executes the block once                 │
└────────────┬──────────────────────────┬─────────────────────┘
             │ call_tool bridge          │ call_tool bridge
             ▼                          ▼
┌────────────────────┐      ┌───────────────────────┐
│  get_policy_details│      │  get_current_offers   │
│  (tools/policy_tool│      │  (tools/offers_tool   │
│   .py)             │      │   .py)                │
└────────┬───────────┘      └──────────┬────────────┘
         │                             │
         ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   database/db.py (mongomock)                │
│           insurance_db.policies  |  insurance_db.products   │
└─────────────────────────────────────────────────────────────┘
```

### Middleware Pipeline

```
agent.run(query)
      │
      ▼
log_tool_calls middleware (pre-call)
      │
      ▼ call_next()
   tool executes (get_policy_details / get_current_offers / execute_code)
      │
      ▼
log_tool_calls middleware (post-call — logs result + elapsed time)
```

---

## Technology Stack

| Component | Package | Version | Role |
|---|---|---|---|
| Agent Framework | `agent-framework-core` | >=1.0.0 | Core MAF agent abstractions |
| CodeAct / Hyperlight | `agent-framework-hyperlight` | >=1.0.0b260709 | Sandboxed code execution provider |
| Hyperlight WASM Backend | `hyperlight-sandbox-backend-wasm` | >=0.5.0 | WASM-based sandbox runtime for Hyperlight |
| Gemini LLM | `agent-framework-gemini` | >=1.0.0a260709 | MAF-native Gemini connector |
| Local DB | `mongomock` | >=4.3.0 | In-memory MongoDB-compatible store |
| Env loading | `python-dotenv` | >=1.2.2 | Loads `.env` variables |
| Package manager | `uv` | — | Fast Python package/project manager |
| Python | — | 3.14.0 | Runtime |

---

## Microsoft Agent Framework (MAF)

MAF is the successor to both **Semantic Kernel** and **AutoGen**, combining:
- AutoGen's simple agent abstractions
- Semantic Kernel's enterprise features (middleware, type safety, telemetry)
- Graph-based workflows for multi-agent orchestration

### Core Concepts Used in This Project

| Concept | Description |
|---|---|
| `Agent` | The main agent class. Takes a `client=` (LLM), `instructions=`, `tools=`, `context_providers=`, and `middleware=` |
| `ContextProvider` | A plugin that modifies the agent's context at runtime (e.g. injects a system prompt fragment and registers tools) |
| `tool` | Decorator that wraps a Python function as an agent-callable tool with JSON schema generation |
| `function_middleware` | Decorator that creates a middleware layer intercepting every tool invocation |
| `FunctionInvocationContext` | Context object passed through the middleware chain with `.function`, `.arguments`, and `.result` |

### The `client=` Parameter Rule

> **Always set the LLM via the `client=` parameter on `Agent`.  
> Never instantiate a Gemini/Claude/OpenAI client and call it directly.**

Reason: passing `client=` routes all LLM calls through MAF's middleware pipeline, enabling telemetry, retries, context management, and safety filters. Calling the Gemini SDK directly bypasses all of that.

```python
# ✅ Correct — goes through MAF middleware
agent = Agent(client=GeminiChatClient(), ...)

# ❌ Wrong — bypasses MAF entirely
import google.generativeai as genai
model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content(...)
```

---

## CodeAct — How It Works

CodeAct is a pattern introduced in the paper *["Executable Code Actions Elicit Better LLM Agents" (Wang et al., 2024)](https://arxiv.org/abs/2402.01030)*.

### Traditional Tool-Calling (5 model turns for a 5-step task)

```
User query
  → Model turn 1: call get_policy_details
  ← Tool result
  → Model turn 2: call get_current_offers
  ← Tool result
  → Model turn 3: analyse gaps (no tool)
  → Model turn 4: rank recommendations
  → Model turn 5: format response
```

**5 round-trips to the LLM = high latency + high token cost.**

### CodeAct (1 model turn for the same task)

```
User query
  → Model turn 1: execute_code (model writes a Python block):
      policy = call_tool("get_policy_details", policy_number="POL-1001")
      offers = call_tool("get_current_offers", policy_type=policy["policy_type"])
      gaps = [o for o in offers if o["name"] not in policy["current_features"]]
      print(gaps)
  ← Hyperlight sandbox runs the block, bridges call_tool() to host tools
  ← Returns consolidated stdout
  → Model turn 2: format final recommendation from stdout
```

**2 model turns regardless of how many tools are called inside the block.**

### How `HyperlightCodeActProvider` Works

`HyperlightCodeActProvider` is a `ContextProvider`. On every `agent.run()` call it:

1. **Registers** a special `execute_code` tool on the agent
2. **Injects** CodeAct instructions into the system prompt, telling the model:
   - A sandbox is available
   - All tools passed to the provider are accessible via `call_tool("name", ...)`
   - How to format the code block

The model then has a choice: call tools directly (traditional) **or** write a Python program that calls them via `call_tool(...)` (CodeAct). For multi-step tasks, it will choose CodeAct.

### Hyperlight Sandbox Security

Each `execute_code` invocation runs in a **fresh Hyperlight micro-VM**:
- No access to the host filesystem (unless `file_mounts=` is configured)
- No network access (unless `allowed_domains=` is configured)
- Startup time is measured in milliseconds (effectively free per call)
- Your tool functions run on the **host**, not inside the sandbox — they keep full access to the database, network, etc.

```
Sandbox (Hyperlight micro-VM)          Host process
┌─────────────────────────────┐        ┌──────────────────┐
│ model-generated Python code │        │                  │
│                             │──────→ │ get_policy_details│
│ call_tool("get_policy_      │ bridge │ (queries mongomock│
│   details", ...)            │←────── │  database)       │
└─────────────────────────────┘        └──────────────────┘
```

---

## Why CodeAct vs Traditional Tool-Calling

| | Traditional | CodeAct |
|---|---|---|
| Model turns per 2-tool query | 3–5 | 1–2 |
| Token usage | High (repeated context) | ~60% lower |
| End-to-end latency | High | ~50% lower |
| Auditability | Spread across messages | Single code block |
| Best for | 1–2 tool calls, side-effecting tools | Chained data lookups, computation |

**Benchmarks from the MAF team** (on an 8-user order-total workload with dozens of tool calls):  
~50% latency reduction, >60% token reduction.

---

## Project Structure

```
MAF-CodeAct/
├── .env                        ← API keys (gitignored)
├── .env.example                ← Template for .env
├── .gitignore
├── .python-version             ← 3.14.0
├── .git/                       ← Version control
├── pyproject.toml              ← UV project manifest
├── uv.lock                     ← Locked dependency versions
├── main.py                     ← Entry point / interactive CLI
├── test_tools.py               ← Standalone tool tests (no pytest required)
│
├── database/
│   ├── __init__.py
│   └── db.py                   ← mongomock client, seeding, get_db()
│
├── tools/
│   ├── __init__.py
│   ├── policy_tool.py          ← @tool get_policy_details(policy_number)
│   └── offers_tool.py          ← @tool get_current_offers(policy_type)
│
├── middleware/
│   ├── __init__.py             ← Re-exports all middleware
│   └── logging_middleware.py   ← @function_middleware log_tool_calls
│
└── docs/
    └── insurance_policy_rd_system.md   ← This file
```

---

## Component Details

### Database Layer

**`database/db.py`**

- Uses `mongomock.MongoClient()` — a pure-Python, in-process, MongoDB-API-compatible client
- Database name: `insurance_db`
- Collections: `policies`, `products`
- Singleton pattern: database is created and seeded exactly once on first `get_db()` call
- `_seed_database()` is called automatically — no separate seeding step needed
- Queries use standard `pymongo` API: `find_one()`, `find()`, `insert_many()`

```python
from database.db import get_db

db = get_db()                            # seeds on first call
policy = db.policies.find_one({"policy_number": "POL-1001"}, {"_id": 0})
offers  = db.products.find({"eligible_policy_types": "Health"}, {"_id": 0})
```

### Tools

Both tools are registered with `@tool(approval_mode="never_require")`, meaning the agent can call them without human approval — appropriate for read-only data lookups.

**`tools/policy_tool.py` — `get_policy_details`**

| Property | Value |
|---|---|
| Input | `policy_number: str` — e.g. `"POL-1001"` |
| Output | Full policy dict or `{"error": "..."}` if not found |
| Side effects | None (read-only) |
| Approval | `never_require` |

**`tools/offers_tool.py` — `get_current_offers`**

| Property | Value |
|---|---|
| Input | `policy_type: str` — `Health`, `Auto`, `Life`, or `Home` |
| Output | List of offer dicts (empty-list equivalent if none found) |
| Side effects | None (read-only) |
| Approval | `never_require` |

Both tools are passed to `HyperlightCodeActProvider(tools=[...])` — **not** directly to `Agent(tools=[...])`. This means:
- The model does **not** see them as direct tools
- It can only reach them by calling `call_tool("name", ...)` inside an `execute_code` block
- This enforces the CodeAct pattern for these data-fetching operations

### Middleware

**`middleware/logging_middleware.py`**

Decorated with `@function_middleware`, which makes it part of MAF's function invocation pipeline. It wraps every tool call:

```
pre-call:   prints function name + arguments (or code block for execute_code)
             ↓
call_next(): actual tool executes
             ↓
post-call:  prints return value (or stdout/stderr for execute_code) + elapsed time
```

Adding more middleware is simply:
1. Create `middleware/new_middleware.py` with `@function_middleware async def ...`
2. Export it from `middleware/__init__.py`
3. Add it to `Agent(middleware=[log_tool_calls, new_middleware])`

### Agent (main.py)

```python
codeact = HyperlightCodeActProvider(
    tools=[get_policy_details, get_current_offers],
    approval_mode="never_require",
)

agent = Agent(
    client=GeminiChatClient(),          # LLM via client= — MAF middleware applies
    name="InsurancePolicyAdvisor",
    instructions=AGENT_INSTRUCTIONS,
    context_providers=[codeact],        # CodeAct registered as context provider
    middleware=[log_tool_calls],        # Function call logging
)
```

---

## Data Model

### Policy Document

```json
{
  "policy_number":    "POL-1001",
  "holder_name":      "Alice Johnson",
  "policy_type":      "Health",
  "start_date":       "2024-01-15",
  "end_date":         "2025-01-14",
  "premium_monthly":  450.00,
  "status":           "Active",
  "coverage_amount":  500000,
  "current_features": ["Basic Hospitalization", "Outpatient Cover"],
  "deductible":       1000
}
```

| Field | Type | Description |
|---|---|---|
| `policy_number` | `str` | Unique identifier — format `POL-XXXX` |
| `holder_name` | `str` | Full name of the policyholder |
| `policy_type` | `str` | One of: `Health`, `Auto`, `Life`, `Home` |
| `start_date` | `str` | ISO date string |
| `end_date` | `str` | ISO date string |
| `premium_monthly` | `float` | Current monthly premium in USD |
| `status` | `str` | `Active` or `Lapsed` |
| `coverage_amount` | `int` | Maximum coverage in USD |
| `current_features` | `list[str]` | Feature names already included |
| `deductible` | `float` | Annual deductible in USD |

### Product / Add-on Document

```json
{
  "product_id":             "PROD-H003",
  "name":                   "Mental Health Cover",
  "eligible_policy_types":  ["Health"],
  "monthly_cost":           60.00,
  "description":            "Therapy sessions, psychiatric consultations, and wellness programs.",
  "category":               "Health Enhancement"
}
```

| Field | Type | Description |
|---|---|---|
| `product_id` | `str` | Unique identifier — format `PROD-XNNN` |
| `name` | `str` | Display name of the add-on |
| `eligible_policy_types` | `list[str]` | Which policy types can use this add-on (note: stored as list in DB, but filtered by exact string match) |
| `monthly_cost` | `float` | Additional monthly premium in USD |
| `description` | `str` | Customer-facing description |
| `category` | `str` | Grouping label for reporting |

---

## Seeded Demo Data

### Policies

| Policy # | Holder | Type | Premium/mo | Current Features |
|---|---|---|---|---|
| POL-1001 | Alice Johnson | Health | $450 | Basic Hospitalization, Outpatient Cover |
| POL-1002 | Bob Martinez | Auto | $180 | Third Party Liability, Theft Cover |
| POL-1003 | Carol Smith | Life | $320 | Term Life Cover |
| POL-1004 | David Lee | Home | $210 | Fire & Flood Cover, Contents Cover |
| POL-1005 | Emma Wilson | Health | $680 | Basic Hospitalization, Outpatient Cover, Dental Cover, Vision Cover |
| POL-1006 | Frank Chen | Auto | $250 | Third Party Liability, Theft Cover, Collision Cover |

### Products & Add-ons

#### Health (5 add-ons)

| Product | Monthly Cost | Description |
|---|---|---|
| Dental Cover | $45 | Routine dental checkups, fillings, and orthodontics |
| Vision Cover | $30 | Annual eye exams, glasses, and contact lenses |
| Mental Health Cover | $60 | Therapy, psychiatric consultations, wellness programs |
| Maternity Cover | $85 | Pre-natal care, delivery, and post-natal support |
| Critical Illness Rider | $120 | Lump-sum payout on cancer, heart attack, or stroke |

#### Auto (4 add-ons)

| Product | Monthly Cost | Description |
|---|---|---|
| Collision Cover | $55 | Repair costs from at-fault accidents |
| Roadside Assistance | $15 | 24/7 towing, battery jump-start, flat tyre, fuel delivery |
| Rental Car Cover | $20 | Daily rental allowance while vehicle is being repaired |
| Gap Insurance | $35 | Covers gap between market value and outstanding loan |

#### Life (3 add-ons + shared Critical Illness)

| Product | Monthly Cost | Description |
|---|---|---|
| Critical Illness Rider | $120 | Shared with Health — lump-sum on critical diagnosis |
| Accidental Death Benefit | $25 | Double payout if death results from accident |
| Disability Income Rider | $75 | Monthly income replacement if permanently disabled |
| Waiver of Premium Rider | $18 | Waives future premiums if policyholder becomes disabled |

#### Home (4 add-ons)

| Product | Monthly Cost | Description |
|---|---|---|
| Jewellery & Valuables Cover | $40 | Jewellery, art, and personal electronics |
| Home Emergency Cover | $25 | Emergency repairs for boilers, plumbing, electrical |
| Liability Cover | $15 | Personal liability for visitor injuries on property |
| Legal Expenses Cover | $20 | Legal costs for property disputes |

---

## Agent Flow — Step by Step

```
1. User enters: POL-1001

2. main.py calls: await agent.run(
     "Analyse policy number POL-1001. Retrieve the policy details and all
      available offers for its policy type, identify coverage gaps, then
      recommend the top 3 add-ons to upsell."
   )

3. Agent sends message to Gemini (via GeminiChatClient → MAF middleware)
   System prompt includes:
     - AGENT_INSTRUCTIONS (role + output format)
     - CodeAct instructions injected by HyperlightCodeActProvider
       (explains execute_code tool + call_tool() pattern)

4. Gemini responds with an execute_code call:
   ┌──────────────────────────────────────────────────────────────┐
   │ policy = call_tool("get_policy_details",                     │
   │              policy_number="POL-1001")                       │
   │ offers = call_tool("get_current_offers",                     │
   │              policy_type=policy["policy_type"])              │
   │ current = policy["current_features"]                         │
   │ gaps = [o for o in offers if o["name"] not in current]       │
   │ print("policy:", policy)                                     │
   │ print("gaps:", gaps)                                         │
   └──────────────────────────────────────────────────────────────┘

5. log_tool_calls middleware (pre): prints the code block above

6. Hyperlight sandbox executes the block:
   - call_tool("get_policy_details") bridges to host process
     → get_policy_details("POL-1001") runs on host
       → mongomock query: db.policies.find_one({"policy_number": "POL-1001"})
       → returns Alice's policy dict
   - call_tool("get_current_offers") bridges to host process
     → get_current_offers("Health") runs on host
       → mongomock query: db.products.find({"eligible_policy_types": "Health"})
       → returns 5 Health add-on dicts
   - gaps analysis runs in sandbox
   - stdout captured: policy dict + gap list

7. log_tool_calls middleware (post): prints stdout + elapsed time

8. Agent sends stdout back to Gemini as the execute_code result

9. Gemini generates final recommendation (1 more model turn)

10. main.py prints the recommendation
```

---

## Middleware Pipeline

The `@function_middleware` decorator registers `log_tool_calls` in MAF's function invocation chain. Every tool call — both `execute_code` and the individual `get_policy_details` / `get_current_offers` calls bridged from the sandbox — passes through this middleware.

**Pre-call output example (execute_code):**
```
────────────────────────────────────────────────────────────
▶  execute_code  (CodeAct sandbox — model-generated Python)
────────────────────────────────────────────────────────────
policy = call_tool("get_policy_details", policy_number="POL-1001")
offers = call_tool("get_current_offers", policy_type=policy["policy_type"])
...
────────────────────────────────────────────────────────────
```

**Post-call output example (execute_code):**
```
stdout:
policy: {'policy_number': 'POL-1001', 'holder_name': 'Alice Johnson', ...}
gaps: [{'name': 'Mental Health Cover', ...}, ...]
  (0.0523s)
```

**Pre/post output for a regular tool call (if called directly):**
```
▶ get_policy_details(policy_number='POL-1001')
◀ get_policy_details → {'policy_number': 'POL-1001', ...}
  (0.0012s)
```

---

## Gemini LLM Integration

The `GeminiChatClient` (from `agent-framework-gemini`) reads credentials from environment variables:

| Env Var | Description |
|---|---|
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Gemini Developer API key from Google AI Studio |
| `GEMINI_MODEL` or `GOOGLE_MODEL` | Model name e.g. `gemini-2.5-flash-lite` |
| `GOOGLE_GENAI_USE_VERTEXAI=true` | Switch to Vertex AI instead of Developer API |
| `GOOGLE_CLOUD_PROJECT` | Vertex AI project ID (if using Vertex AI) |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region (if using Vertex AI) |

```python
# Zero-arg constructor — reads all config from env vars
client = GeminiChatClient()
```

Recommended models (in order of cost/performance):

| Model | Speed | Cost | Best for |
|---|---|---|---|
| `gemini-2.5-flash-lite` | Fastest | Lowest | Dev/demo |
| `gemini-2.5-flash` | Fast | Medium | Production |
| `gemini-2.5-pro` | Slower | Highest | Complex reasoning |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.5-flash-lite
```

Get your API key from: https://aistudio.google.com/apikey  
The `.env` file is gitignored and will never be committed.

---

## Setup & Running

### Prerequisites

- Python 3.14+ (set in `.python-version`)
- [uv](https://docs.astral.sh/uv/) package manager
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- **[Hyperlight/WSL2 Setup Guide](./hyperlight-wsl2-kvm-setup.md)** completed (if on Windows; macOS and Linux users see [Platform Compatibility](#platform-compatibility) section for notes)

> **⚠️ If you are on Windows, the Hyperlight setup guide is MANDATORY.** Do not skip it. See [Platform Compatibility](#platform-compatibility) above.

### Install

```bash
# 1. Create virtual environment (already done if .venv/ exists)
uv venv .venv

# 2. Install all dependencies
uv sync
# or if packages not yet in pyproject.toml:
uv add --prerelease=allow agent-framework-gemini agent-framework-hyperlight mongomock python-dotenv

# 3. Create your .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and GEMINI_MODEL
```

### Run the DB seeding test

```bash
uv run python database/db.py
```

Expected output:
```
[DB] Seeded 6 policies and 16 products.

── Policies ──
{'policy_number': 'POL-1001', 'holder_name': 'Alice Johnson', 'policy_type': 'Health'}
...

── Products ──
{'product_id': 'PROD-H001', 'name': 'Dental Cover', 'eligible_policy_types': ['Health']}
...
```

### Run the tools in isolation

```bash
uv run python test_tools.py
```

Expected output: 5 test scenarios showing policy lookups and offer retrieval.

Alternatively, invoke tools programmatically:

```bash
uv run python -c "
from tools.policy_tool import get_policy_details
from tools.offers_tool import get_current_offers
print(get_policy_details.func('POL-1001'))
print(get_current_offers.func('Health'))
"
```

**Note:** Use `.func()` to call the underlying tool function directly, or `.invoke()` to call through the MAF tool wrapper.

### Run the full system (interactive demo)

```bash
uv run python main.py
```

Then enter a policy number at the prompt, e.g. `POL-1001`.

The system will:
1. Print the available demo policies
2. Wait for your input
3. Use the agent to analyse the policy and recommend add-ons
4. Display the CodeAct-generated Python block showing how the sandbox executed
5. Print the advisor's recommendation

Type `quit`, `exit`, or `q` to exit at any time, or press `Ctrl+C`.

---

## Expected Output

```
════════════════════════════════════════════════════════════
  Insurance Policy R&D System
  Powered by Microsoft Agent Framework + CodeAct + Gemini
════════════════════════════════════════════════════════════

Available demo policies:
  POL-1001  Alice Johnson   — Health  ($450/mo)
  POL-1002  Bob Martinez    — Auto    ($180/mo)
  ...

Enter policy number: POL-1001

════════════════════════════════════════════════════════════
  INSURANCE POLICY R&D ADVISOR  —  CodeAct Demo
════════════════════════════════════════════════════════════
Query : Analyse policy number POL-1001. ...

────────────────────────────────────────────────────────────
▶  execute_code  (CodeAct sandbox — model-generated Python)
────────────────────────────────────────────────────────────
policy = call_tool("get_policy_details", policy_number="POL-1001")
offers = call_tool("get_current_offers", policy_type=policy["policy_type"])
current = policy["current_features"]
gaps = [o for o in offers if o["name"] not in current]
print("policy:", policy)
print("gaps:", gaps)
────────────────────────────────────────────────────────────
stdout:
policy: {'policy_number': 'POL-1001', 'holder_name': 'Alice Johnson', ...}
gaps: [{'name': 'Mental Health Cover', ...}, {'name': 'Maternity Cover', ...}, ...]
  (0.0612s)

════════════════════════════════════════════════════════════
  ADVISOR RECOMMENDATION
════════════════════════════════════════════════════════════

**Policy Summary**
- Holder: Alice Johnson
- Type: Health | Status: Active
- Current Premium: $450/month
- Existing Features: Basic Hospitalization, Outpatient Cover

**Top 3 Recommended Add-ons**

1. **Critical Illness Rider** (+$120/mo)
   Provides a lump-sum payout on cancer, heart attack, or stroke —
   the most common catastrophic health events. High value for the customer,
   highest revenue impact.

2. **Mental Health Cover** (+$60/mo)
   Growing demand; therapy and psychiatric consultations are increasingly
   common claims. Proactive recommendation builds customer loyalty.

3. **Maternity Cover** (+$85/mo)
   Given Alice's age profile and life stage, maternity cover is a natural fit.

**Projected New Monthly Premium: $715**  
**Annual Revenue Increase for Insurer: $3,180**
```

---

## Extending the System

### Add a new policy type (e.g. Travel)

1. Add travel policies to `database/db.py` → `policies` list
2. Add travel products to `database/db.py` → `products` list with `"eligible_policy_types": ["Travel"]`
3. Run `uv run python test_tools.py` to verify the new data is seeded
4. No changes to tools, middleware, or agent needed

### Add a new tool (e.g. get_claim_history)

1. Create `tools/claim_tool.py` with `@tool(approval_mode="never_require") def get_claim_history(...)`
2. Import and add to `HyperlightCodeActProvider(tools=[..., get_claim_history])`
3. Update `AGENT_INSTRUCTIONS` to mention the new tool

### Add new middleware (e.g. audit logging to file)

1. Create `middleware/audit_middleware.py` with `@function_middleware async def audit_log(...)`
2. Export from `middleware/__init__.py`: `from middleware.audit_middleware import audit_log`
3. Add to `Agent(middleware=[log_tool_calls, audit_log])`

### Switch to persistent MongoDB

Replace the `mongomock.MongoClient()` in `database/db.py` with a real `pymongo.MongoClient`:

```python
import pymongo
_client = pymongo.MongoClient("mongodb://localhost:27017/")
```

No other changes needed — the rest of the codebase uses the standard pymongo API.

---

## Design Decisions

| Decision | Choice | Reasoning |
|---|---|---|
| CodeAct vs traditional tools | CodeAct via `HyperlightCodeActProvider` | The policy query + offers lookup is exactly the multi-step chained lookup pattern CodeAct excels at — collapses 3+ model turns into 1 |
| LLM client | `GeminiChatClient(client=...)` | Follows MAF contract — all LLM calls go through middleware. Gemini is free-tier accessible for demos |
| Database | `mongomock` | Zero-install, cross-platform, MongoDB-API-compatible. For production, swap for real MongoDB by changing one line |
| Middleware location | `middleware/` package | Separation of concerns + extensible. Adding middleware = drop a file + one export line |
| Tools on provider, not agent | `HyperlightCodeActProvider(tools=[...])` | Forces CodeAct pattern — model must use `execute_code` to call tools, demonstrating the sandbox correctly |
| Approval mode | `never_require` | Read-only data tools. Side-effecting tools (e.g. email, purchase) should use `always_require` |
| Singleton DB | Module-level `_client` | mongomock is in-memory; re-seeding on every call would reset state. Singleton gives consistent state for the session |
