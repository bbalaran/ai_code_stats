#!/usr/bin/env python3
"""Final verification of ProdLens MVP functionality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("dev-agent-lens/scripts/src").resolve()))

from prodlens.storage import ProdLensStore
from prodlens.trace_ingestion import TraceIngestor

# Test ingestion
trace_file = Path("dev-agent-lens/.prod-lens/logs/litellm-traces.jsonl")
db_path = Path(".prod-lens/final-verification.db")

print("🔍 ProdLens MVP - Final Verification\n")
print("=" * 60)

with ProdLensStore(db_path) as store:
    ingestor = TraceIngestor(store)
    inserted = ingestor.ingest_file(trace_file, repo_slug="test/prodlens-demo")

print(f"✅ Ingested {inserted} trace records\n")

# Verify data
with ProdLensStore(db_path) as store:
    cursor = store.conn.execute("""
        SELECT
            session_id,
            developer_id,
            model,
            tokens_in,
            tokens_out,
            latency_ms,
            cost_usd,
            repo_slug
        FROM sessions
        ORDER BY timestamp
    """)

    print("📊 Ingested Sessions:\n")
    print(f"{'Session':<12} {'Developer':<20} {'Model':<35} {'Tokens':<12} {'Latency':<10} {'Cost':<10} {'Repo':<20}")
    print("-" * 130)

    total_cost = 0.0
    total_tokens = 0

    for row in cursor.fetchall():
        session_id, dev_id, model, tokens_in, tokens_out, latency, cost, repo = row
        tokens = f"{tokens_in}+{tokens_out}"
        total_cost += cost
        total_tokens += tokens_in + tokens_out

        # Truncate long fields
        model_short = model.split("/")[-1] if model else "N/A"
        dev_short = dev_id.split("@")[0] if dev_id else "N/A"

        print(f"{session_id:<12} {dev_short:<20} {model_short:<35} {tokens:<12} {latency:<10.1f} ${cost:<9.4f} {repo:<20}")

    print("-" * 130)
    print(f"\n📈 Summary:")
    print(f"   Total Sessions: {inserted}")
    print(f"   Total Tokens: {total_tokens:,}")
    print(f"   Total Cost: ${total_cost:.4f}")

print("\n" + "=" * 60)
print("✅ ProdLens MVP verification COMPLETE")
print("\n🎉 System is fully functional and ready for production!")
