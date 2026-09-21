# scylla-mem0-demo

Workshop material for ScyllaDB + mem0.

## Stack

- **mem0** — installed from a fork
  ([zseta/mem0@main](https://github.com/zseta/mem0)) with the
  not-yet-merged [ScyllaDB vector store PR #5373](https://github.com/mem0ai/mem0/pull/5373)
  applied on top of upstream `main`. Switch back to plain `mem0ai` from PyPI
  once that PR merges (see `pyproject.toml`).
- **ScyllaDB** (2025.4+, required for native vector search / SAI) — vector store
  backing mem0's semantic memory search. History store stays on mem0's SQLite
  default (this PR doesn't cover history/graph stores).
- **Gemini** (`gemini-2.5-flash`) — LLM used by mem0 for fact extraction. mem0's
  extraction prompt runs ~8k tokens on its own, which fits comfortably inside
  Gemini's free-tier budget (250k tokens/minute) but would eat most of Groq's
  free-tier cap (8k tokens/minute) in a single call — hence Gemini. A small
  retry-with-backoff (`core/retry.py`) absorbs occasional rate-limit hits.
- **HuggingFace (`sentence-transformers`)** — local embedding model
  (`multi-qa-MiniLM-L6-cos-v1`, 384 dims), no external embeddings API needed.
- **Streamlit** — interactive dashboard driving its own scenario runs.
- **Rich** — CLI output.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Docker + Docker Compose
- A Gemini API key, free, at [aistudio.google.com](https://aistudio.google.com/apikey)

## Setup

1. Copy `.env.example` to `.env` and fill in `GOOGLE_API_KEY`:

   ```bash
   cp .env.example .env
   ```

2. Start the 3-node ScyllaDB cluster:

   ```bash
   docker compose up -d
   ```

   Wait ~30-60s for all nodes to become healthy:

   ```bash
   docker compose ps
   docker exec -it scylla-node1 nodetool status
   ```

3. Install dependencies:

   ```bash
   uv sync
   ```

4. Confirm `SCYLLA_CONTACT_POINTS` in `.env` points at your cluster (defaults
   to `127.0.0.1` for the local Docker setup above).

5. Pre-seed the three demo personas' behavioral history into mem0:

   ```bash
   uv run python -m txmonitor.seed
   ```

## Running the demo

**CLI** — scripted walkthrough for all three personas, printing the mem0
lookup latency and decision for each transaction:

```bash
uv run python -m txmonitor.cli.run
```

**Streamlit dashboard** — pick a persona and step through their scenario
interactively:

```bash
uv run streamlit run src/txmonitor/streamlit_app.py
```

## Switching to ScyllaDB Cloud

Everything is driven by `.env` — point these at your cloud cluster instead of
the local Docker one:

```
SCYLLA_CONTACT_POINTS=<your-cloud-node-ips>
SCYLLA_USERNAME=<...>
SCYLLA_PASSWORD=<...>
SCYLLA_DATACENTER=<...>   # required for ScyllaDB Cloud DC-aware routing
```

This demo does not use SSL/TLS (`use_ssl` is left at the ScyllaDBConfig default
of `False`, so no cert path is configured either).

## Project layout

```
src/txmonitor/
  core/
    memory_client.py   mem0 Memory config: Gemini + HuggingFace + ScyllaDB
    rules.py            rule-based anomaly checks (plain config constants)
    processor.py         ties recall + rule check together, times the lookup
  cli/run.py            CLI scenario runner
  streamlit_app.py      Streamlit dashboard
  seed.py                pre-seeds persona history into mem0
data/personas/personas.py  3 personas: seed history + scripted scenario
docker-compose.yml       3-node ScyllaDB cluster
```
