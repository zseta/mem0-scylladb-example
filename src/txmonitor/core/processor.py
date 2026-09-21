"""Ties together mem0 recall and rule-based decisioning for one transaction,
timing the memory lookup so its latency can be shown live."""

import re
import time
from dataclasses import dataclass

from txmonitor.core.rules import Decision, Transaction, check_transaction

AMOUNT_RE = re.compile(r"\$?(\d+(?:\.\d+)?)")


@dataclass
class ProcessingResult:
    transaction: Transaction
    decision: Decision
    recalled_facts: list
    lookup_latency_ms: float
    typical_amount: float
    known_locations: set


def _extract_typical_amount(facts: list) -> float:
    amounts = []
    for fact in facts:
        for match in AMOUNT_RE.findall(fact):
            amounts.append(float(match))
    return max(amounts) if amounts else 0.0


def _extract_known_locations(facts: list, known_locations_seed: set) -> set:
    locations = set(known_locations_seed)
    for fact in facts:
        for loc in known_locations_seed:
            if loc.lower() in fact.lower():
                locations.add(loc)
    return locations


def process_transaction(
    memory,
    transaction: Transaction,
    known_locations_seed: set,
    known_categories_seed: set,
) -> ProcessingResult:
    """Recall this user's behavioral facts from mem0 and judge the transaction against them.

    The recall call is timed in isolation, since that's the latency the
    workshop demo is about: whether "what's normal for this user" can be
    fetched fast enough to sit in the hot path of a real-time decision.
    """
    start = time.perf_counter()
    search_result = memory.search(
        f"typical spending amount, location, and merchant category for this user",
        filters={"user_id": transaction.user_id},
        top_k=10,
    )
    lookup_latency_ms = (time.perf_counter() - start) * 1000

    facts = [r["memory"] for r in search_result.get("results", [])]

    typical_amount = _extract_typical_amount(facts)
    known_locations = _extract_known_locations(facts, known_locations_seed)

    decision = check_transaction(
        transaction,
        typical_amount=typical_amount,
        known_locations=known_locations,
        known_categories=known_categories_seed,
    )

    return ProcessingResult(
        transaction=transaction,
        decision=decision,
        recalled_facts=facts,
        lookup_latency_ms=lookup_latency_ms,
        typical_amount=typical_amount,
        known_locations=known_locations,
    )
