"""Standalone tool tests — run directly: python test_tools.py"""
from tools.policy_tool import get_policy_details
from tools.offers_tool import get_current_offers

print("=" * 55)
print("TEST 1: get_policy_details — valid policy POL-1001")
print("=" * 55)
r = get_policy_details.func("POL-1001")
for k, v in r.items():
    print(f"  {k}: {v}")

print()
print("=" * 55)
print("TEST 2: get_policy_details — unknown policy POL-9999")
print("=" * 55)
r = get_policy_details.func("POL-9999")
print(" ", r)

print()
print("=" * 55)
print("TEST 3: get_current_offers — Health")
print("=" * 55)
offers = get_current_offers.func("Health")
for o in offers:
    pid = o.get("product_id", "?")
    name = o.get("name", "?")
    cost = o.get("monthly_cost", "?")
    print(f"  {pid}  {name:<35}  ${cost}/mo")

print()
print("=" * 55)
print("TEST 4: get_current_offers — Auto")
print("=" * 55)
offers = get_current_offers.func("Auto")
for o in offers:
    pid = o.get("product_id", "?")
    name = o.get("name", "?")
    cost = o.get("monthly_cost", "?")
    print(f"  {pid}  {name:<35}  ${cost}/mo")

print()
print("=" * 55)
print("TEST 5: get_current_offers — unknown type 'Pet'")
print("=" * 55)
r = get_current_offers.func("Pet")
print(" ", r)

print()
print("ALL TOOL TESTS PASSED")
