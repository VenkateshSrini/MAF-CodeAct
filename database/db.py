"""
MongoDB-compliant local document store using mongomock.
Provides a seeded in-memory database with insurance policies and product offers.
Works on both Windows and Linux — no MongoDB server required.
"""

from __future__ import annotations

from typing import Any

import mongomock

_client: mongomock.MongoClient | None = None


def get_db() -> mongomock.Database:
    """Return the singleton mongomock database, seeding it on first access."""
    global _client
    if _client is None:
        _client = mongomock.MongoClient()
        _seed_database(_client)
    return _client["insurance_db"]


def _seed_database(client: mongomock.MongoClient) -> None:
    """Seed the database with demo insurance policies and available add-on products."""
    db = client["insurance_db"]
    db.policies.drop()
    db.products.drop()

    policies: list[dict[str, Any]] = [
        {
            "policy_number": "POL-1001",
            "holder_name": "Alice Johnson",
            "policy_type": "Health",
            "start_date": "2024-01-15",
            "end_date": "2025-01-14",
            "premium_monthly": 450.00,
            "status": "Active",
            "coverage_amount": 500000,
            "current_features": ["Basic Hospitalization", "Outpatient Cover"],
            "deductible": 1000,
        },
        {
            "policy_number": "POL-1002",
            "holder_name": "Bob Martinez",
            "policy_type": "Auto",
            "start_date": "2024-03-01",
            "end_date": "2025-02-28",
            "premium_monthly": 180.00,
            "status": "Active",
            "coverage_amount": 50000,
            "current_features": ["Third Party Liability", "Theft Cover"],
            "deductible": 500,
        },
        {
            "policy_number": "POL-1003",
            "holder_name": "Carol Smith",
            "policy_type": "Life",
            "start_date": "2023-06-10",
            "end_date": "2043-06-09",
            "premium_monthly": 320.00,
            "status": "Active",
            "coverage_amount": 1000000,
            "current_features": ["Term Life Cover"],
            "deductible": 0,
        },
        {
            "policy_number": "POL-1004",
            "holder_name": "David Lee",
            "policy_type": "Home",
            "start_date": "2024-05-20",
            "end_date": "2025-05-19",
            "premium_monthly": 210.00,
            "status": "Active",
            "coverage_amount": 300000,
            "current_features": ["Fire & Flood Cover", "Contents Cover"],
            "deductible": 750,
        },
        {
            "policy_number": "POL-1005",
            "holder_name": "Emma Wilson",
            "policy_type": "Health",
            "start_date": "2024-02-01",
            "end_date": "2025-01-31",
            "premium_monthly": 680.00,
            "status": "Active",
            "coverage_amount": 750000,
            "current_features": [
                "Basic Hospitalization",
                "Outpatient Cover",
                "Dental Cover",
                "Vision Cover",
            ],
            "deductible": 500,
        },
        {
            "policy_number": "POL-1006",
            "holder_name": "Frank Chen",
            "policy_type": "Auto",
            "start_date": "2024-04-15",
            "end_date": "2025-04-14",
            "premium_monthly": 250.00,
            "status": "Active",
            "coverage_amount": 75000,
            "current_features": [
                "Third Party Liability",
                "Theft Cover",
                "Collision Cover",
            ],
            "deductible": 300,
        },
    ]

    products: list[dict[str, Any]] = [
        # ── Health add-ons ─────────────────────────────────────────────
        {
            "product_id": "PROD-H001",
            "name": "Dental Cover",
            "eligible_policy_types": ["Health"],
            "monthly_cost": 45.00,
            "description": "Routine dental checkups, fillings, and orthodontics.",
            "category": "Health Enhancement",
        },
        {
            "product_id": "PROD-H002",
            "name": "Vision Cover",
            "eligible_policy_types": ["Health"],
            "monthly_cost": 30.00,
            "description": "Annual eye exams, prescription glasses, and contact lenses.",
            "category": "Health Enhancement",
        },
        {
            "product_id": "PROD-H003",
            "name": "Mental Health Cover",
            "eligible_policy_types": ["Health"],
            "monthly_cost": 60.00,
            "description": "Therapy sessions, psychiatric consultations, and wellness programs.",
            "category": "Health Enhancement",
        },
        {
            "product_id": "PROD-H004",
            "name": "Maternity Cover",
            "eligible_policy_types": ["Health"],
            "monthly_cost": 85.00,
            "description": "Pre-natal care, delivery, and post-natal support.",
            "category": "Health Enhancement",
        },
        {
            "product_id": "PROD-H005",
            "name": "Critical Illness Rider",
            "eligible_policy_types": ["Health", "Life"],
            "monthly_cost": 120.00,
            "description": "Lump-sum payout on diagnosis of cancer, heart attack, or stroke.",
            "category": "Critical Cover",
        },
        # ── Auto add-ons ───────────────────────────────────────────────
        {
            "product_id": "PROD-A001",
            "name": "Collision Cover",
            "eligible_policy_types": ["Auto"],
            "monthly_cost": 55.00,
            "description": "Covers repair costs from at-fault accidents.",
            "category": "Auto Enhancement",
        },
        {
            "product_id": "PROD-A002",
            "name": "Roadside Assistance",
            "eligible_policy_types": ["Auto"],
            "monthly_cost": 15.00,
            "description": "24/7 towing, battery jump-start, flat tyre, and fuel delivery.",
            "category": "Auto Enhancement",
        },
        {
            "product_id": "PROD-A003",
            "name": "Rental Car Cover",
            "eligible_policy_types": ["Auto"],
            "monthly_cost": 20.00,
            "description": "Daily rental car allowance while your vehicle is being repaired.",
            "category": "Auto Enhancement",
        },
        {
            "product_id": "PROD-A004",
            "name": "Gap Insurance",
            "eligible_policy_types": ["Auto"],
            "monthly_cost": 35.00,
            "description": "Covers the gap between car market value and outstanding loan.",
            "category": "Auto Enhancement",
        },
        # ── Life add-ons ───────────────────────────────────────────────
        {
            "product_id": "PROD-L001",
            "name": "Accidental Death Benefit",
            "eligible_policy_types": ["Life"],
            "monthly_cost": 25.00,
            "description": "Double payout if death results from an accident.",
            "category": "Life Enhancement",
        },
        {
            "product_id": "PROD-L002",
            "name": "Disability Income Rider",
            "eligible_policy_types": ["Life"],
            "monthly_cost": 75.00,
            "description": "Monthly income replacement if permanently disabled.",
            "category": "Life Enhancement",
        },
        {
            "product_id": "PROD-L003",
            "name": "Waiver of Premium Rider",
            "eligible_policy_types": ["Life"],
            "monthly_cost": 18.00,
            "description": "Waives future premiums if policyholder becomes disabled.",
            "category": "Life Enhancement",
        },
        # ── Home add-ons ───────────────────────────────────────────────
        {
            "product_id": "PROD-HO001",
            "name": "Jewellery & Valuables Cover",
            "eligible_policy_types": ["Home"],
            "monthly_cost": 40.00,
            "description": "High-value items: jewellery, art, and personal electronics.",
            "category": "Home Enhancement",
        },
        {
            "product_id": "PROD-HO002",
            "name": "Home Emergency Cover",
            "eligible_policy_types": ["Home"],
            "monthly_cost": 25.00,
            "description": "Emergency repairs for boilers, plumbing, and electrical faults.",
            "category": "Home Enhancement",
        },
        {
            "product_id": "PROD-HO003",
            "name": "Liability Cover",
            "eligible_policy_types": ["Home"],
            "monthly_cost": 15.00,
            "description": "Personal liability if a visitor is injured on your property.",
            "category": "Home Enhancement",
        },
        {
            "product_id": "PROD-HO004",
            "name": "Legal Expenses Cover",
            "eligible_policy_types": ["Home"],
            "monthly_cost": 20.00,
            "description": "Legal costs for property disputes and contract issues.",
            "category": "Home Enhancement",
        },
    ]

    db.policies.insert_many(policies)
    db.products.insert_many(products)
    print(f"[DB] Seeded {len(policies)} policies and {len(products)} products.")


if __name__ == "__main__":
    # Run standalone to verify seeding
    db = get_db()
    print("\n── Policies ──")
    for p in db.policies.find({}, {"_id": 0, "policy_number": 1, "holder_name": 1, "policy_type": 1}):
        print(p)
    print("\n── Products ──")
    for p in db.products.find({}, {"_id": 0, "product_id": 1, "name": 1, "eligible_policy_types": 1}):
        print(p)
