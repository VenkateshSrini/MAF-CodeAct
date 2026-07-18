# Insurance Policy R&D System

> **AI-powered upsell recommendation engine using Microsoft Agent Framework (MAF) + CodeAct + Google Gemini**

---

## ⚠️ Platform Notice — Windows Users READ FIRST

**If you are on Windows**, you **MUST** use WSL2 and complete the [Hyperlight/WSL2 Setup Guide](docs/hyperlight-wsl2-kvm-setup.md) **BEFORE** trying to run this project.

- ✅ **macOS & Linux:** Works out of the box
- ✅ **Windows 11 + WSL2:** Full support (setup guide required)
- ❌ **Native Windows:** Not supported (Hyperlight sandbox creation will fail)

See the [Platform Compatibility](docs/insurance_policy_rd_system.md#platform-compatibility) section in the full docs for details.

---

## Quick Start

### 1. Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- **Windows only:** [Hyperlight/WSL2 Setup Guide](docs/hyperlight-wsl2-kvm-setup.md) completed

### 2. Install

```bash
# Create virtual environment and install dependencies
uv venv .venv
uv sync

# Create .env file with your API credentials
cp .env.example .env
# Edit .env and add GEMINI_API_KEY and GEMINI_MODEL
```

### 3. Run

```bash
# Test the database and tools
uv run python test_tools.py

# Run the interactive demo
uv run python main.py
```

---

## What This System Does

Given a **policy number**, the system:

1. **Retrieves** the full policy record
2. **Fetches** all available add-on products for that policy type
3. **Identifies** coverage gaps
4. **Recommends** the top 3 best add-ons to upsell with:
   - Value explanation for the customer
   - Monthly cost of each add-on
   - Projected new premium
   - Estimated annual revenue increase for the insurer

**Demo policies included:** POL-1001 through POL-1006

---

## Technology Stack

- **Agent Framework:** Microsoft Agent Framework (MAF)
- **CodeAct/Sandboxing:** Hyperlight (via `HyperlightCodeActProvider`)
- **LLM:** Google Gemini (via `agent-framework-gemini`)
- **Database:** mongomock (in-memory MongoDB-compatible)
- **Language:** Python 3.14.0

---

## Documentation

📖 **Full documentation with architecture, design decisions, and extension guides:**

### [→ View Full Documentation](docs/insurance_policy_rd_system.md)

The complete guide includes:

- ✅ [Platform Compatibility](docs/insurance_policy_rd_system.md#platform-compatibility) — Windows/macOS/Linux setup requirements
- ✅ [Architecture Overview](docs/insurance_policy_rd_system.md#architecture) — System design and data flow
- ✅ [Technology Stack](docs/insurance_policy_rd_system.md#technology-stack) — Detailed component versions
- ✅ [CodeAct Explanation](docs/insurance_policy_rd_system.md#codeact--how-it-works) — How CodeAct reduces LLM turns
- ✅ [Component Details](docs/insurance_policy_rd_system.md#component-details) — Database, tools, middleware
- ✅ [Data Model](docs/insurance_policy_rd_system.md#data-model) — Policy and product schemas
- ✅ [Agent Flow](docs/insurance_policy_rd_system.md#agent-flow--step-by-step) — Step-by-step execution walkthrough
- ✅ [Setup Instructions](docs/insurance_policy_rd_system.md#setup--running) — Complete installation guide
- ✅ [Testing Guide](docs/insurance_policy_rd_system.md#testing) — How to test tools in isolation
- ✅ [Expected Output](docs/insurance_policy_rd_system.md#expected-output) — Sample output examples
- ✅ [Extending the System](docs/insurance_policy_rd_system.md#extending-the-system) — How to add new features
- ✅ [Design Decisions](docs/insurance_policy_rd_system.md#design-decisions) — Rationale behind choices

---

## Project Structure

```
MAF-CodeAct/
├── README.md                           ← You are here
├── main.py                             ← Entry point (interactive CLI)
├── test_tools.py                       ← Tool testing (no pytest required)
├── pyproject.toml                      ← Dependencies
├── .env.example                        ← Environment template
│
├── database/
│   └── db.py                           ← mongomock setup & seeding
│
├── tools/
│   ├── policy_tool.py                  ← Get policy details
│   └── offers_tool.py                  ← Get available offers
│
├── middleware/
│   └── logging_middleware.py           ← Function call logging
│
└── docs/
    ├── insurance_policy_rd_system.md   ← FULL DOCUMENTATION
    └── hyperlight-wsl2-kvm-setup.md    ← Windows WSL2 setup guide
```

---

## Usage Example

```bash
$ uv run python main.py

════════════════════════════════════════════════════════════
  Insurance Policy R&D System
  Powered by Microsoft Agent Framework + CodeAct + Gemini
════════════════════════════════════════════════════════════

Available demo policies:
  POL-1001  Alice Johnson   — Health  ($450/mo)
  POL-1002  Bob Martinez    — Auto    ($180/mo)
  ...

Enter policy number: POL-1001

[Agent analyses policy using CodeAct sandbox...]

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
   High value for the customer, highest revenue impact.

2. **Mental Health Cover** (+$60/mo)
   Growing demand; builds customer loyalty.

3. **Maternity Cover** (+$85/mo)
   Natural fit for Alice's life stage.

**Projected New Monthly Premium: $715**
**Annual Revenue Increase for Insurer: $3,180**
```

---

## Key Features

- 🎯 **CodeAct Pattern** — Reduces LLM turns from 5 to 2 for multi-tool queries
- 🔒 **Sandboxed Execution** — Hyperlight micro-VMs for secure code execution
- 🧠 **Intelligent Analysis** — Gemini LLM identifies coverage gaps and ranks recommendations
- 📦 **No External DB** — mongomock provides MongoDB-compatible in-memory storage
- 🔧 **Extensible** — Easy to add new tools, middleware, or policy types
- 📋 **Zero Dependencies** — Works on Windows (WSL2), macOS, and Linux

---

## Troubleshooting

### "Failed to create sandbox: No Hypervisor was found for Sandbox"

**If on Windows:** Follow the [Hyperlight/WSL2 Setup Guide](docs/hyperlight-wsl2-kvm-setup.md) to enable KVM in WSL2.

**If on macOS/Linux:** Check that virtualization is enabled in BIOS and the system has KVM or HyperKit support.

### "GEMINI_API_KEY is not set"

Create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API key from https://aistudio.google.com/apikey
```

### "Policy not found"

Use one of the demo policies: POL-1001 to POL-1006.

---

## Next Steps

1. **Read the full documentation:** [insurance_policy_rd_system.md](docs/insurance_policy_rd_system.md)
2. **If on Windows:** Complete [hyperlight-wsl2-kvm-setup.md](docs/hyperlight-wsl2-kvm-setup.md)
3. **Run tests:** `uv run python test_tools.py`
4. **Run the system:** `uv run python main.py`

---

## License

This project is provided as-is for educational and demonstration purposes.

---

**Questions?** See the [full documentation](docs/insurance_policy_rd_system.md) or check the [troubleshooting section](#troubleshooting) above.
