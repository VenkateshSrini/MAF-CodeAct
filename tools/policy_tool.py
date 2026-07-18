"""Tool: get_policy_details — retrieves a single policy from the local document store."""

from __future__ import annotations

from typing import Annotated, Any

from agent_framework import tool

from database.db import get_db


@tool(approval_mode="never_require")
def get_policy_details(
    policy_number: Annotated[str, "The policy number to look up, e.g. POL-1001."],
) -> dict[str, Any]:
    """Retrieve full details of an insurance policy by its policy number.

    Returns a dictionary containing: policy_number, holder_name, policy_type,
    start_date, end_date, premium_monthly, status, coverage_amount,
    current_features, and deductible.
    Returns an error dictionary if the policy is not found.
    """
    db = get_db()
    policy = db.policies.find_one(
        {"policy_number": policy_number.strip().upper()},
        {"_id": 0},
    )
    if policy is None:
        return {"error": f"Policy '{policy_number}' not found. Valid examples: POL-1001 to POL-1006."}
    return dict(policy)
