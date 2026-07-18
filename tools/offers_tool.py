"""Tool: get_current_offers — retrieves available add-on products for a policy type."""

from __future__ import annotations

from typing import Annotated, Any

from agent_framework import tool

from database.db import get_db


@tool(approval_mode="never_require")
def get_current_offers(
    policy_type: Annotated[
        str,
        "The type of insurance policy. Must be one of: Health, Auto, Life, or Home.",
    ],
) -> list[dict[str, Any]]:
    """Retrieve all available add-on products and riders for a given policy type.

    Returns a list of offer dictionaries, each containing:
    product_id, name, monthly_cost, description, and category.
    These represent features that can be added to increase coverage and premium.
    """
    db = get_db()
    offers = list(
        db.products.find(
            {"eligible_policy_types": policy_type.strip().title()},
            {"_id": 0},
        )
    )
    if not offers:
        return [{"message": f"No offers found for policy type '{policy_type}'. Valid types: Health, Auto, Life, Home."}]
    return offers
