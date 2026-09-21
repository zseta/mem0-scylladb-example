"""Builds the mem0 Memory instance backed by Gemini (LLM), a local HuggingFace
embedder, and ScyllaDB (vector store)."""

import os

from mem0 import Memory

# multi-qa-MiniLM-L6-cos-v1 (mem0's HuggingFace embedder default) outputs
# 384-dim vectors. The ScyllaDB vector store table is created with this
# dimension, so it must match the embedder exactly.
EMBEDDING_MODEL_DIMS = 384


def build_memory_config() -> dict:
    contact_points = [
        p.strip() for p in os.getenv("SCYLLA_CONTACT_POINTS", "127.0.0.1").split(",") if p.strip()
    ]

    scylladb_config = {
        "contact_points": contact_points,
        "port": int(os.getenv("SCYLLA_PORT", "9042")),
        "keyspace": os.getenv("SCYLLA_KEYSPACE", "mem0"),
        "collection_name": "transaction_memories",
        "embedding_model_dims": EMBEDDING_MODEL_DIMS,
    }

    username = os.getenv("SCYLLA_USERNAME") or None
    password = os.getenv("SCYLLA_PASSWORD") or None
    if username and password:
        scylladb_config["username"] = username
        scylladb_config["password"] = password

    datacenter = os.getenv("SCYLLA_DATACENTER") or None
    if datacenter:
        scylladb_config["datacenter"] = datacenter

    return {
        "vector_store": {
            "provider": "scylladb",
            "config": scylladb_config,
        },
        "llm": {
            "provider": "gemini",
            "config": {
                # mem0's fact-extraction prompt alone runs ~8k tokens, which
                # exceeds Groq's 8000 TPM free-tier cap on plain chat models
                # for this account. Gemini's free tier caps at 250k TPM.
                "model": "gemini-2.5-flash",
                "api_key": os.getenv("GOOGLE_API_KEY"),
            },
        },
        "embedder": {
            "provider": "huggingface",
            "config": {
                "model": "multi-qa-MiniLM-L6-cos-v1",
                "embedding_dims": EMBEDDING_MODEL_DIMS,
            },
        },
    }


def build_memory() -> Memory:
    """Construct a mem0 Memory instance wired to Gemini + local HF embeddings + ScyllaDB."""
    return Memory.from_config(build_memory_config())
