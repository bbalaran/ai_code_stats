#!/usr/bin/env python3
"""Test end-to-end ProdLens workflow with LiteLLM proxy."""

import json
import os
import sys
import time
from pathlib import Path

# Test making a call through LiteLLM proxy
def test_proxy_call():
    """Test making an API call through the LiteLLM proxy."""
    import anthropic

    # Configure to use LiteLLM proxy
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        base_url="http://localhost:4000"  # LiteLLM proxy
    )

    print("🧪 Testing API call through LiteLLM proxy...")

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say hello in exactly 5 words."}
            ]
        )

        print(f"✅ API call successful!")
        print(f"   Response: {message.content[0].text}")
        print(f"   Tokens: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def check_trace_file():
    """Check if LiteLLM generated trace logs."""
    trace_dir = Path("dev-agent-lens/.prod-lens/logs")

    print("\n🔍 Checking for trace files...")

    if not trace_dir.exists():
        print(f"❌ Trace directory not found: {trace_dir}")
        return None

    # Look for JSONL trace files
    trace_files = list(trace_dir.glob("*.jsonl"))

    if not trace_files:
        print(f"⚠️  No .jsonl trace files found in {trace_dir}")
        print(f"   Directory contents: {list(trace_dir.iterdir())}")
        return None

    # Use most recent trace file
    latest_trace = max(trace_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ Found trace file: {latest_trace}")

    # Read and display last few lines
    with open(latest_trace, "r") as f:
        lines = f.readlines()
        if lines:
            print(f"   Total records: {len(lines)}")
            print(f"   Last record preview:")
            try:
                last_record = json.loads(lines[-1])
                print(f"      Model: {last_record.get('model')}")
                print(f"      Tokens: {last_record.get('usage', {})}")
            except json.JSONDecodeError:
                print(f"      {lines[-1][:100]}...")

    return latest_trace


def test_ingestion(trace_file):
    """Test ingesting traces into ProdLens."""
    if not trace_file:
        print("\n⚠️  Skipping ingestion test (no trace file)")
        return False

    print(f"\n📥 Testing trace ingestion...")

    sys.path.insert(0, str(Path("dev-agent-lens/scripts/src").resolve()))

    from prodlens.storage import ProdLensStore
    from prodlens.trace_ingestion import TraceIngestor

    db_path = Path(".prod-lens/test-e2e-cache.db")

    try:
        with ProdLensStore(db_path) as store:
            ingestor = TraceIngestor(store)
            inserted = ingestor.ingest_file(trace_file, repo_slug="test/e2e-workflow")

        print(f"✅ Ingested {inserted} trace records into {db_path}")

        # Verify data was stored
        with ProdLensStore(db_path) as store:
            cursor = store.conn.execute(
                "SELECT session_id, model, tokens_in, tokens_out, cost_usd FROM sessions ORDER BY timestamp DESC LIMIT 5"
            )
            rows = cursor.fetchall()

            print(f"\n📊 Retrieved {len(rows)} sessions from database:")
            for row in rows:
                print(f"   Session: {row[0]}")
                print(f"      Model: {row[1]}")
                print(f"      Tokens: {row[2]} in, {row[3]} out")
                print(f"      Cost: ${row[4]:.6f}")

        return True

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 ProdLens End-to-End Workflow Test\n")
    print("=" * 60)

    # Check if proxy is running
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        proxy_running = sock.connect_ex(("localhost", 4000)) == 0

    if not proxy_running:
        print("❌ LiteLLM proxy is not running on port 4000")
        print("   Start it with: ./start-litellm-proxy.sh")
        return 1

    print("✅ LiteLLM proxy is running\n")

    # Step 1: Make API call through proxy
    if not test_proxy_call():
        return 1

    # Wait a moment for trace to be written
    time.sleep(2)

    # Step 2: Check for trace files
    trace_file = check_trace_file()

    # Step 3: Ingest traces
    if not test_ingestion(trace_file):
        return 1

    print("\n" + "=" * 60)
    print("✅ End-to-end workflow test PASSED")
    print("\nProdLens is ready for production use!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
