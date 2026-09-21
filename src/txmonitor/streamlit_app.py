"""Streamlit dashboard: pick a persona, step through their scripted
transaction scenario, and watch the mem0 lookup latency + decision live.

Drives its own run against the core processor directly (not tailing the CLI).
"""

import random
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data" / "personas"))

from personas import PERSONAS  # noqa: E402

from txmonitor.core.memory_client import build_memory  # noqa: E402
from txmonitor.core.processor import process_transaction  # noqa: E402
from txmonitor.core.retry import with_rate_limit_retry  # noqa: E402
from txmonitor.core.rules import Transaction  # noqa: E402

load_dotenv()

st.set_page_config(page_title="Transaction Monitoring — ScyllaDB + mem0", layout="centered")
st.title("E-Commerce Fraud Detection")
st.caption("We remember each customer's normal spending habits, then flag any new purchase that doesn't fit — in real time.")

with st.expander("What happens when a transaction is added"):
    st.markdown(
        "- The new purchase is turned into a plain-English sentence "
        "(e.g. *\"Made a purchase of $45 at Lagos (electronics)...\"*) and sent to "
        "**mem0's `memory.add()`**.\n"
        "- mem0 sends that sentence to **Gemini** (`gemini-2.5-flash`) using its built-in "
        "fact-extraction prompt, which pulls out clean behavioral facts "
        "(e.g. *\"User typically spends ~$45\"*, *\"User shops in Lagos\"*) — this is the only "
        "LLM call in the whole flow, and it's just summarization, not a fraud judgment.\n"
        "- Each extracted fact is turned into a vector embedding locally, using a "
        "HuggingFace model (`multi-qa-MiniLM-L6-cos-v1`) — no network call for this step.\n"
        "- mem0 writes the fact text + its embedding into **ScyllaDB**, scoped to that "
        "customer's `user_id`.\n"
        "- On the *next* purchase, **`memory.search()`** runs a vector similarity search "
        "against ScyllaDB to recall that customer's relevant facts — this is the "
        "mem0/ScyllaDB lookup whose latency is timed and shown live.\n"
        "- Those recalled facts (typical amount, known locations/categories) are handed to "
        "plain Python rules that flag the purchase — no LLM involved at decision time."
    )


@st.cache_resource(show_spinner=False)
def get_memory():
    return build_memory()


# build_memory() is expensive the first time a process calls it: it imports
# sentence-transformers and loads the local HF embedder (~10s), then opens
# the ScyllaDB connection and provisions schema. st.cache_resource makes
# every call after the first one instant, so we pay that cost here, up
# front on page load, instead of silently inside the "Run next transaction"
# button handler.
with st.spinner("Warming up mem0 (loading embedder, connecting to ScyllaDB)..."):
    get_memory()

personas_by_id = {p["user_id"]: p for p in PERSONAS}

# Pools to draw unseen locations/categories from when simulating fraud — kept
# separate from any persona's known_locations/known_categories so a "fraud"
# pick is guaranteed to trip the unseen-location/category rule.
FRAUD_LOCATIONS = ["Lagos", "Manila", "Kyiv", "Jakarta", "Nairobi", "Bucharest"]
FRAUD_CATEGORIES = ["electronics", "jewelry", "casino", "wire transfer", "crypto exchange"]
FRAUD_DESCRIPTIONS = [
    "Late-night electronics store purchase",
    "Large jewelry store purchase",
    "Casino cash advance",
    "Overseas wire transfer",
    "Crypto exchange deposit",
]

NORMAL_DESCRIPTIONS_BY_CATEGORY = {
    "groceries": "Grocery run",
    "coffee shop": "Coffee",
    "restaurant": "Dinner out",
    "gas station": "Gas fill-up",
    "hardware store": "Hardware store run",
    "fast food": "Quick lunch",
    "gym": "Gym membership",
    "bookstore": "Bookstore visit",
    "pharmacy": "Pharmacy pickup",
}


def make_normal_transaction(user_id: str, persona: dict) -> Transaction:
    """A plausible in-pattern transaction: known location/category, amount
    close to what the persona's history establishes as typical."""
    location = random.choice(sorted(persona["known_locations"]))
    category = random.choice(sorted(persona["known_categories"]))
    base_amounts = [float(a) for step in persona["scenario"] for a in [step["amount"]] if step["merchant_category"] == category]
    base = base_amounts[0] if base_amounts else 50.0
    amount = round(base * random.uniform(0.85, 1.15), 2)
    description = NORMAL_DESCRIPTIONS_BY_CATEGORY.get(category, "Routine purchase")
    return Transaction(
        user_id=user_id, amount=amount, location=location,
        merchant_category=category, description=description,
    )


def make_fraud_transaction(user_id: str, persona: dict) -> Transaction:
    """An out-of-pattern transaction: unseen location + category, and an
    amount several multiples of anything in the persona's scripted history."""
    max_known_amount = max((step["amount"] for step in persona["scenario"]), default=50.0)
    amount = round(max_known_amount * random.uniform(8, 25), 2)
    location = random.choice(FRAUD_LOCATIONS)
    category = random.choice(FRAUD_CATEGORIES)
    description = random.choice(FRAUD_DESCRIPTIONS)
    return Transaction(
        user_id=user_id, amount=amount, location=location,
        merchant_category=category, description=description,
    )


def run_transaction(memory, user_id: str, persona: dict, transaction: Transaction) -> None:
    """Score a transaction against mem0-recalled history, persist it back to
    mem0, and append the result to this persona's on-screen log."""
    result = process_transaction(
        memory,
        transaction,
        known_locations_seed=persona["known_locations"],
        known_categories_seed=persona["known_categories"],
    )

    with_rate_limit_retry(
        memory.add,
        f"Made a purchase of ${transaction.amount:.2f} at {transaction.location} "
        f"({transaction.merchant_category}): {transaction.description}."
        + (" This was flagged as unusual." if result.decision.flagged else ""),
        user_id=user_id,
    )

    st.session_state.log[user_id].append(result)


if "step_index" not in st.session_state:
    st.session_state.step_index = {}
if "log" not in st.session_state:
    st.session_state.log = {}

user_id = st.selectbox("Persona", list(personas_by_id.keys()))
persona = personas_by_id[user_id]
scenario = persona["scenario"]

st.session_state.step_index.setdefault(user_id, 0)
st.session_state.log.setdefault(user_id, [])

step_index = st.session_state.step_index[user_id]
done = step_index >= len(scenario)

col1, col2 = st.columns(2)
with col1:
    run_disabled = done
    if st.button("Run next transaction", disabled=run_disabled, type="primary", use_container_width=True):
        memory = get_memory()
        step = scenario[step_index]
        transaction = Transaction(
            user_id=user_id,
            amount=step["amount"],
            location=step["location"],
            merchant_category=step["merchant_category"],
            description=step["description"],
        )
        run_transaction(memory, user_id, persona, transaction)
        st.session_state.step_index[user_id] += 1
        st.rerun()

with col2:
    if st.button("Reset persona's scenario progress", use_container_width=True):
        st.session_state.step_index[user_id] = 0
        st.session_state.log[user_id] = []
        st.rerun()

if done and scenario:
    st.success(f"All {len(scenario)} scripted transactions for {user_id} have been played.")

st.caption("Or drive it yourself — throw a plausible purchase or an obvious fraud pattern at it, or write your own.")

col3, col4 = st.columns(2)
with col3:
    if st.button("🟢 Simulate normal transaction", use_container_width=True):
        memory = get_memory()
        transaction = make_normal_transaction(user_id, persona)
        run_transaction(memory, user_id, persona, transaction)
        st.rerun()

with col4:
    if st.button("🔴 Simulate fraud transaction", use_container_width=True):
        memory = get_memory()
        transaction = make_fraud_transaction(user_id, persona)
        run_transaction(memory, user_id, persona, transaction)
        st.rerun()

with st.expander("✏️ Write your own transaction"):
    with st.form(key="custom_transaction_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            custom_amount = st.number_input("Amount ($)", min_value=0.01, value=50.00, step=1.00)
            custom_location = st.text_input("Location", value="Seattle")
        with c2:
            custom_category = st.text_input("Merchant category", value="groceries")
            custom_description = st.text_input("Description", value="Custom purchase")

        submitted = st.form_submit_button("Submit transaction", type="primary")
        if submitted:
            memory = get_memory()
            transaction = Transaction(
                user_id=user_id,
                amount=custom_amount,
                location=custom_location.strip() or "Unknown",
                merchant_category=custom_category.strip() or "unknown",
                description=custom_description.strip() or "Custom purchase",
            )
            run_transaction(memory, user_id, persona, transaction)
            st.rerun()

st.divider()

for i, result in enumerate(reversed(st.session_state.log[user_id])):
    t = result.transaction
    with st.container(border=True):
        st.markdown(f"**{t.description}** — ${t.amount:.2f} @ {t.location} ({t.merchant_category})")

        if result.decision.flagged:
            st.error("FLAGGED")
            for reason in result.decision.reasons:
                st.markdown(f"- {reason}")
        else:
            st.success("APPROVED")

        st.caption(
            f"From memory: typical amount ~${result.typical_amount:.2f}, "
            f"known locations: {', '.join(sorted(result.known_locations)) or 'none yet'}"
        )

        with st.expander(f"{len(result.recalled_facts)} facts recalled from mem0"):
            for fact in result.recalled_facts:
                st.markdown(f"- {fact}")
