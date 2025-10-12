#!/bin/bash
# Start LiteLLM Proxy for ProdLens trace collection

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$SCRIPT_DIR/litellm_config.yaml"
LOG_DIR="$SCRIPT_DIR/.prod-lens/logs"
TRACE_LOG="$LOG_DIR/litellm-traces.jsonl"

# Create log directory
mkdir -p "$LOG_DIR"

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable not set"
    echo "Please set it with: export ANTHROPIC_API_KEY='sk-ant-...'"
    exit 1
fi

# Set optional database URL if not set
export DATABASE_URL="${DATABASE_URL:-sqlite:///$SCRIPT_DIR/.prod-lens/litellm.db}"
export STORE_MODEL_IN_DB="${STORE_MODEL_IN_DB:-True}"

echo "🚀 Starting LiteLLM Proxy..."
echo "   Config: $CONFIG_FILE"
echo "   Database: $DATABASE_URL"
echo "   Port: 4000"
echo "   Logs: $LOG_DIR"
echo ""

# Start LiteLLM proxy with config (simple mode - no workers, no database)
# Remove DATABASE_URL to avoid Prisma requirement
unset DATABASE_URL
unset STORE_MODEL_IN_DB

# Set log directory for custom callback
export LITELLM_LOG_DIR="$LOG_DIR"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

exec litellm \
    --config "$CONFIG_FILE" \
    --port 4000 \
    --debug
