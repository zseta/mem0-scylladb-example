"""Rule-based anomaly checks, evaluated against behavioral facts recalled from mem0.

No LLM call happens here — the whole point of the demo is that the flag/pass
decision is made in plain code, in the same latency budget as the memory lookup.
"""

from dataclasses import dataclass, field

# Tune these live during the workshop to show how the thresholds change outcomes.
AMOUNT_MULTIPLIER_THRESHOLD = 3.0
UNSEEN_LOCATION_IS_SUSPICIOUS = True
UNSEEN_MERCHANT_CATEGORY_IS_SUSPICIOUS = True


@dataclass
class Transaction:
    user_id: str
    amount: float
    location: str
    merchant_category: str
    description: str


@dataclass
class Decision:
    flagged: bool
    reasons: list = field(default_factory=list)


def check_transaction(transaction: Transaction, typical_amount: float, known_locations: set, known_categories: set) -> Decision:
    reasons = []

    if typical_amount and transaction.amount > typical_amount * AMOUNT_MULTIPLIER_THRESHOLD:
        reasons.append(
            f"amount ${transaction.amount:.2f} is {transaction.amount / typical_amount:.1f}x "
            f"the typical ${typical_amount:.2f}"
        )

    if UNSEEN_LOCATION_IS_SUSPICIOUS and known_locations and transaction.location not in known_locations:
        reasons.append(f"location '{transaction.location}' not seen before (known: {sorted(known_locations)})")

    if (
        UNSEEN_MERCHANT_CATEGORY_IS_SUSPICIOUS
        and known_categories
        and transaction.merchant_category not in known_categories
    ):
        reasons.append(f"merchant category '{transaction.merchant_category}' not seen before")

    return Decision(flagged=bool(reasons), reasons=reasons)
