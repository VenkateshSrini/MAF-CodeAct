"""Insurance Policy R&D System — Microsoft Agent Framework + CodeAct + Gemini.

Entry point for the interactive CLI. The agent uses HyperlightCodeActProvider
as a ContextProvider so the model generates a single Python code block that
calls both tools inside the Hyperlight sandbox instead of making separate
round-trips for each tool.

Required environment variables (set in .env):
    GEMINI_API_KEY   — Google AI Studio API key
    GEMINI_MODEL     — e.g. gemini-2.5-flash-lite or gemini-2.5-pro
"""

from __future__ import annotations

import asyncio
import os
import sys

from agent_framework import Agent
from agent_framework.hyperlight import HyperlightCodeActProvider
from agent_framework_gemini import GeminiChatClient
from dotenv import load_dotenv

from middleware import log_tool_calls
from tools.offers_tool import get_current_offers
from tools.policy_tool import get_policy_details

load_dotenv()

_CYAN = "\033[36m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_LINE = "═" * 60

AGENT_INSTRUCTIONS = """\
You are an expert Insurance Policy R&D Advisor working for an insurer.

Your goal is to analyse a policyholder's current coverage and identify
the best add-on products to recommend so the insurer can increase revenue.

Follow these steps precisely using the tools available inside execute_code:
1. Call get_policy_details to retrieve the full policy record.
2. Call get_current_offers with the policy_type from step 1.
3. Compare current_features against all available offers to find gaps.
4. Select the top 3 add-ons the policyholder does NOT yet have, ranked by
   value delivered to the customer AND revenue impact for the insurer.

Format your final response as:
- Policy summary (holder, type, current premium, existing features)
- Top 3 Recommended Add-ons (name, monthly cost, why it suits this customer)
- New projected monthly premium after all 3 are added
- Estimated annual revenue increase for the insurer
"""


def _validate_env() -> bool:
    """Check required environment variables are present before running."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GEMINI_MODEL") or os.getenv("GOOGLE_MODEL")
    if not key:
        print("ERROR: GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.")
        print("       Add it to a .env file in the project root.")
        return False
    if not model:
        print("ERROR: GEMINI_MODEL (or GOOGLE_MODEL) is not set.")
        print("       Example: GEMINI_MODEL=gemini-2.5-flash-lite")
        return False
    return True


async def run_analysis(policy_number: str) -> None:
    """Run a full R&D analysis for one policy number using MAF CodeAct."""
    # Register both tools on the CodeAct provider so the model calls them
    # from inside a single execute_code sandbox turn (CodeAct pattern).
    codeact = HyperlightCodeActProvider(
        tools=[get_policy_details, get_current_offers],
        approval_mode="never_require",
    )

    # LLM is passed via client= — GeminiChatClient reads GEMINI_API_KEY and
    # GEMINI_MODEL from env. This goes through MAF middleware, not raw Gemini SDK.
    agent = Agent(
        client=GeminiChatClient(),
        name="InsurancePolicyAdvisor",
        instructions=AGENT_INSTRUCTIONS,
        context_providers=[codeact],
        middleware=[log_tool_calls],
    )

    query = (
        f"Analyse policy number {policy_number.strip().upper()}. "
        "Retrieve the policy details and all available offers for its policy type, "
        "identify coverage gaps, then recommend the top 3 add-ons to upsell."
    )

    print(f"\n{_CYAN}{_BOLD}{_LINE}")
    print("  INSURANCE POLICY R&D ADVISOR  —  CodeAct Demo")
    print(f"{_LINE}{_RESET}")
    print(f"{_CYAN}Query : {query}{_RESET}\n")

    result = await agent.run(query)

    print(f"\n{_CYAN}{_BOLD}{_LINE}")
    print("  ADVISOR RECOMMENDATION")
    print(f"{_LINE}{_RESET}")
    print(f"{_CYAN}{result.text}{_RESET}\n")


async def main() -> None:
    """Interactive CLI — enter a policy number or type 'quit' to exit."""
    if not _validate_env():
        sys.exit(1)

    print(f"\n{_BOLD}{'═' * 60}")
    print("  Insurance Policy R&D System")
    print("  Powered by Microsoft Agent Framework + CodeAct + Gemini")
    print(f"{'═' * 60}{_RESET}")
    print("\nAvailable demo policies:")
    print("  POL-1001  Alice Johnson   — Health  ($450/mo)")
    print("  POL-1002  Bob Martinez    — Auto    ($180/mo)")
    print("  POL-1003  Carol Smith     — Life    ($320/mo)")
    print("  POL-1004  David Lee       — Home    ($210/mo)")
    print("  POL-1005  Emma Wilson     — Health  ($680/mo, already has more features)")
    print("  POL-1006  Frank Chen      — Auto    ($250/mo, already has Collision Cover)")
    print("\nType 'quit' to exit.\n")

    while True:
        try:
            policy_number = input("Enter policy number: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if policy_number.lower() in ("quit", "exit", "q"):
            break
        if not policy_number:
            continue
        await run_analysis(policy_number)


if __name__ == "__main__":
    asyncio.run(main())
