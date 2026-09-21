"""Pre-seeded personas: behavioral history to load into mem0 before the live
demo, plus the scripted transaction sequence played back during the demo.

Each persona's `history` is a list of natural-language messages describing past
transactions — these get added to mem0 via `memory.add(...)` so mem0's LLM
extracts durable facts (typical amount, usual locations/categories) from them.
`known_locations` / `known_categories` are the ground truth used by the rule
checker; they mirror what a careful reading of `history` should establish.
"""

PERSONAS = [
    {
        "user_id": "alice",
        "known_locations": {"Seattle", "Bellevue"},
        "known_categories": {"groceries", "coffee shop", "restaurant"},
        "history": [
            "Bought groceries for $85.20 at a Seattle supermarket.",
            "Paid $6.50 for coffee at a coffee shop in Seattle.",
            "Had dinner at a restaurant in Bellevue for $62.00.",
            "Bought groceries for $92.10 at a Seattle supermarket.",
            "Paid $5.75 for coffee at a coffee shop in Seattle.",
            "Had dinner at a restaurant in Seattle for $78.40.",
            "Bought groceries for $88.60 at a Seattle supermarket.",
            "Paid $6.25 for coffee at a coffee shop in Bellevue.",
        ],
        "scenario": [
            {"amount": 91.00, "location": "Seattle", "merchant_category": "groceries",
             "description": "Weekly grocery run"},
            {"amount": 6.00, "location": "Seattle", "merchant_category": "coffee shop",
             "description": "Morning coffee"},
            {"amount": 2400.00, "location": "Lagos", "merchant_category": "electronics",
             "description": "Electronics store purchase"},
        ],
    },
    {
        "user_id": "bob",
        "known_locations": {"Austin", "Round Rock"},
        "known_categories": {"gas station", "hardware store", "fast food"},
        "history": [
            "Filled up gas for $45.00 at a gas station in Austin.",
            "Bought tools for $120.00 at a hardware store in Austin.",
            "Grabbed lunch for $11.50 at a fast food restaurant in Austin.",
            "Filled up gas for $48.30 at a gas station in Round Rock.",
            "Bought supplies for $75.00 at a hardware store in Austin.",
            "Grabbed lunch for $9.80 at a fast food restaurant in Austin.",
            "Filled up gas for $42.75 at a gas station in Austin.",
        ],
        "scenario": [
            {"amount": 46.50, "location": "Austin", "merchant_category": "gas station",
             "description": "Regular fill-up"},
            {"amount": 15.00, "location": "Round Rock", "merchant_category": "fast food",
             "description": "Lunch stop"},
            {"amount": 890.00, "location": "Austin", "merchant_category": "jewelry",
             "description": "Jewelry store purchase"},
        ],
    },
    {
        "user_id": "carla",
        "known_locations": {"Denver", "Boulder"},
        "known_categories": {"gym", "bookstore", "pharmacy"},
        "history": [
            "Paid $55.00 for a gym membership renewal in Denver.",
            "Bought books for $32.40 at a bookstore in Boulder.",
            "Bought medication for $18.90 at a pharmacy in Denver.",
            "Paid $55.00 for a gym membership renewal in Denver.",
            "Bought books for $28.00 at a bookstore in Denver.",
            "Bought vitamins for $22.50 at a pharmacy in Boulder.",
        ],
        "scenario": [
            {"amount": 56.00, "location": "Denver", "merchant_category": "gym",
             "description": "Monthly gym renewal"},
            {"amount": 24.00, "location": "Boulder", "merchant_category": "pharmacy",
             "description": "Pharmacy pickup"},
            {"amount": 3100.00, "location": "Miami", "merchant_category": "electronics",
             "description": "Electronics store purchase"},
        ],
    },
]
