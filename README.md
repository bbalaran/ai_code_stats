# misc

Monorepo containing multiple AI development and observability projects.

## Projects

### 🔍 Dev Agent Lens
AI development observability framework with trace export, session analysis, and performance metrics.

- **Location**: `dev-agent-lens/`
- **CLI**: `uv run dev-agent-lens/scripts/main.py [command]`
- **Commands**:
  - `export` - Export trace data (auto-detects Arize or Phoenix)
  - `analyze` - Analyze session reconstruction
  - `reconstruct` - Reconstruct sessions from traces
  - `compare` - Compare spans to identify duplication patterns
  - `prod-lens` - ProdLens analytics toolkit (see below)
- **Docs**: `dev-agent-lens/docs/`

#### ProdLens MVP v1.2
Analytics toolkit built on Dev Agent Lens for correlating AI interactions with software delivery outcomes.

- **Location**: `dev-agent-lens/scripts/src/prodlens/`
- **CLI**: `prod-lens [command]` or `./prod-lens [command]` (from project root)
- **Commands**:
  - `ingest-traces <file.jsonl>` - Ingest LiteLLM proxy traces
  - `ingest-github --repo owner/name` - Sync GitHub PR/commit data
  - `report --repo owner/name --since YYYY-MM-DD` - Generate analytics report
- **Features**:
  - LiteLLM trace ingestion with cost estimation
  - GitHub API synchronization with ETag caching
  - Statistical correlation analysis (Pearson, Spearman)
  - Dead-letter queue for error recovery
  - JSON and CSV export formats
- **Docs**: `dev-agent-lens/docs/PRODLENS_TECHNICAL_SPEC.md`
- **Quality**: 8.0/10 (production-ready after Phase 1 fixes)
- **Test Coverage**: 11/11 tests passing

### 📚 Other Projects
- **lemmy/**: Lemmy API integration and utilities

## Quick Start

```bash
# Install dependencies (from dev-agent-lens/scripts)
cd dev-agent-lens/scripts
pip install -e .

# Use unified CLI
uv run main.py --help

# Or use prod-lens directly from root
./prod-lens --help

# Example: Ingest traces and generate report
./prod-lens ingest-traces traces.jsonl --repo myorg/myrepo
./prod-lens ingest-github --repo myorg/myrepo
./prod-lens report --repo myorg/myrepo --since 2024-01-01
```

## Documentation

- **PR Guidelines**: `docs/pr-guidelines/` - Code review patterns and anti-patterns
- **ProdLens Spec**: `dev-agent-lens/docs/PRODLENS_TECHNICAL_SPEC.md`
- **Review Analysis**: `prod-lens-consultation/` - External AI consultation reports