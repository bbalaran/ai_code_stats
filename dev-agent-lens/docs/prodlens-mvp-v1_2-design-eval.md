# ProdLens MVP v1.2 Design Evaluation and Update

## 1. Executive Summary
ProdLens MVP v1.2 is intended to help engineering leaders understand how AI-assisted development activities correlate with downstream software delivery outcomes. Evaluating the design against the open-source Dev-Agent-Lens stack in this repository confirms that the overall direction is compatible with the available tracing proxy, LiteLLM routing, and observability integrations, yet several implementation specifics require clarification so the MVP can be piloted on top of the actual components. The updated plan below preserves the v1.2 focus on statistical rigor (time-aligned and lagged significance testing), adds a reliability layer for GitHub and trace ingestion, and explicitly scopes work around the capabilities shipped in Dev-Agent-Lens (e.g., Claude Code CLI proxy, Arize/Phoenix telemetry, example SDK integrations). The pilot target remains a 5–10 developer cohort over two weeks, with success defined as identifying at least one statistically significant association or delivering an NPS of four or higher from 80% of participants. Key adjustments include:

- Aligning the logging and ingestion strategy with the proxy and example clients provided in `dev-agent-lens`, ensuring trace collection works for both CLI and SDK-based sessions while maintaining parity between local and cloud pilots.
- Clarifying how LiteLLM’s proxy configuration, OpenTelemetry exporters, and Arize/Phoenix sinks supply the required data fields for correlation and efficiency metrics, including token totals, latency histograms, and error codes.
- Hardening GitHub ETL with SQLite-backed checkpoints plus ETag conditional requests to stay within API budgets while supporting daily lagged calculations and re-run safety.
- Documenting reproducible installation steps built on top of the repository’s Docker Compose profiles and example environments so pilots can be reproduced quickly by internal or customer teams.
- Expanding qualitative signal capture (experience sampling) so that “why” insights are gathered alongside quantitative outcomes, aiding interpretation of statistically significant associations.

The following sections detail the metrics, architecture, tech stack, integration points, and operational practices required to operationalize ProdLens MVP v1.2 on this codebase.

### 1.1 Explicit Metrics Provided
The MVP will collect and compute the following quantitative indicators on a daily cadence, with lagged comparisons where appropriate:

- **AI Interaction Velocity** – Median latency between command issuance and AI response, and total trace count per engineer-hour; threshold: >4 sessions/hour, <30 second median latency.
- **Acceptance Rate** – Percentage of AI-generated suggestions that match accepted code diffs (>0.7 difflib ratio); threshold: >25%.
- **Model Selection Accuracy** – Fraction of sessions where the engineer chooses a model aligned with internal policy (e.g., Sonnet for secure branches); threshold: >80%.
- **Error Rate** – Share of sessions terminating with LiteLLM or downstream proxy errors; threshold: <5%.
- **Token Efficiency** – Tokens per accepted line and cost per merged PR (<50 tokens/line, <$0.50/PR).
- **PR Throughput** – Merged pull requests per team per week (>5/wk/team).
- **Commit Frequency** – Commits per active day (>10/day/dev) acknowledging pilot team scale.
- **PR Merge Time** – Hours between PR creation and merge (<24 hrs) serving as a DORA lead-time proxy.
- **Rework Rate** – Percentage of merged PRs reopened within 21 days (<22%).
- **AI-Outcome Association** – Lagged Pearson/Spearman correlations with p-values (e.g., AI sessions today vs. commits tomorrow, significant when p < 0.05).

## 2. Table of Contents
- [1. Executive Summary](#1-executive-summary)
  - [1.1 Explicit Metrics Provided](#11-explicit-metrics-provided)
- [2. Table of Contents](#2-table-of-contents)
- [3. Tech Stack in Detail](#3-tech-stack-in-detail)
  - [3.1 Data Ingestion and Tracing](#31-data-ingestion-and-tracing)
  - [3.2 Storage and Caching](#32-storage-and-caching)
  - [3.3 Analytics and Correlation Engine](#33-analytics-and-correlation-engine)
  - [3.4 Deployment Tooling](#34-deployment-tooling)
- [4. All the APIs and Integration Points](#4-all-the-apis-and-integration-points)
  - [4.1 LiteLLM Proxy API](#41-litellm-proxy-api)
  - [4.2 OpenTelemetry Exporters (Arize AX & Phoenix)](#42-opentelemetry-exporters-arize-ax--phoenix)
  - [4.3 GitHub REST API](#43-github-rest-api)
  - [4.4 CLI and SDK Integration Points](#44-cli-and-sdk-integration-points)
  - [4.5 Optional Integrations](#45-optional-integrations)
- [5. Additional Implementation Details](#5-additional-implementation-details)
  - [5.1 Data Pipeline Walkthrough](#51-data-pipeline-walkthrough)
  - [5.2 Pilot Execution Plan](#52-pilot-execution-plan)
  - [5.3 Risk Mitigation](#53-risk-mitigation)
  - [5.4 Roadmap Considerations](#54-roadmap-considerations)
  - [5.5 Documentation Deliverables](#55-documentation-deliverables)

## 3. Tech Stack in Detail

### 3.1 Data Ingestion and Tracing
ProdLens will leverage the Claude Code proxy workflow already present in Dev-Agent-Lens. The [`claude-lens` wrapper](../README.md) ships with OAuth passthrough and defaults to routing API calls through LiteLLM on `localhost:4000`, making it a drop-in telemetry source for pilot engineers. The proxy surfaces OpenTelemetry spans that can be exported to Arize AX or Phoenix (local) depending on Docker profile, satisfying the MVP’s need for session-level metadata, token counts, and latency measurements (see [README.md](../README.md) for details).

To support SDK-driven automations (e.g., documentation generator, code review agent) the examples in [`examples/python`](../examples/python) and [`examples/typescript`](../examples/typescript) also route through the proxy by default. This ensures that synthetic or automated sessions can be captured for regression testing or backfill, without diverging from live telemetry paths (see [README.md](../README.md) for details). ProdLens must therefore ship parser utilities that ingest LiteLLM request/response JSONL emitted by the proxy or exported via Arize/Phoenix, normalizing fields such as `usage.total_tokens`, latency attributes, tool invocation metadata, and trace/span identifiers. Normalization should output a canonical schema (`session_id`, `developer_id`, `timestamp`, `model`, `tokens_in`, `tokens_out`, `latency_ms`, `status_code`, `accepted_flag`) persisted as parquet to enable incremental recomputation without reprocessing the raw spans.

Because the proxy already emits rich span attributes, the ingestion job should enforce schema validation (e.g., via Pydantic) and include dead-letter queues for malformed payloads. This guarantees that correlation routines operate on consistent, trustworthy data even when upstream services change response formats.

### 3.2 Storage and Caching
The design retains the `.prod-lens/cache.db` SQLite file to store GitHub pull request, commit, and checkpoint metadata. This is aligned with the minimal-dependency philosophy of Dev-Agent-Lens (Dockerized services for observability, otherwise local tooling) and avoids introducing additional infrastructure during pilot. Checkpoint tables track the latest synchronized `merged_at`/`pushed_at` timestamps to support delta fetches. For trace ingestion, a thin parquet or SQLite table can be appended with session-level statistics (token counts, model, status, acceptance flag). Because LiteLLM and the examples already emphasize local-first development, storing caches within the repo directory will not conflict with expected usage patterns.

Cache tables should include composite indexes on `(repo_slug, day)` and `(session_id)` to accelerate incremental updates and deduplicate data. An auxiliary `etl_runs` table records execution timestamps, input parameters, and row counts to aid observability and rollback. When pilots scale, this schema can be migrated to Postgres with minimal adjustment by reusing SQLAlchemy models generated for SQLite.

### 3.3 Analytics and Correlation Engine
Python remains the primary analytics runtime, leveraging `pandas`, `scipy`, and `difflib` per the existing code snippet. The analyzer operates as a CLI command `prod-lens report --repo org/repo --since YYYY-MM-DD`, reading cached GitHub data and normalized trace records to produce CSV/CLI outputs. Lagged Pearson/Spearman correlations are run on daily aggregates with configurable offsets (e.g., sessions vs. next-day commits). Given the pilot size, results will be considered reliable when each lagged series contains at least six non-null pairs, aligning with standard practices for exploratory correlations.

To prevent misinterpretation, the CLI should annotate each reported correlation with sample size, effect size translation (percentage delta compared to baseline), and multiple-comparison adjustments (e.g., Benjamini–Hochberg) when more than three hypotheses are tested simultaneously. Visualizations (ASCII sparkline or optional HTML report) can accompany the numeric output to make trend shifts obvious during stakeholder readouts.

### 3.4 Deployment Tooling
Deployment piggybacks on the repository’s Docker Compose profiles. Teams choose between `docker compose --profile arize up -d` (cloud telemetry) or `--profile phoenix` (local). See the [observability backend setup guide](../README.md#2-choose-your-observability-backend) for details. ProdLens scripts should detect which profile is active by checking exposed ports (4000 for LiteLLM, 6006 for Phoenix UI) and adjust export destinations accordingly. CLI distribution can reuse the existing `claude-lens` installation workflow (`sudo cp claude-lens /usr/local/bin`), while analytics run through a Python virtual environment (e.g., `uv` or `pip`) listed in `requirements.txt` to be added alongside this design.

Environment management should highlight reproducibility: pin Python dependencies via `uv pip compile`, provide `Makefile` targets (`make setup`, `make report`), and ship container images for air-gapped clients leveraging the same base images as Dev-Agent-Lens Docker services. Observability dashboards (Arize/Phoenix) need seeded templates stored under `docs/dashboards/` with import instructions to avoid manual configuration drift.

## 4. All the APIs and Integration Points

### 4.1 LiteLLM Proxy API
- **Purpose**: Intercepts Claude Code CLI and SDK requests, applies policy, and emits observability metadata via OpenTelemetry.
- **Endpoints Used**:
  - `POST /v1/messages` (Claude Code messaging).
  - `GET /health` for readiness checks when triggering batch analyses.
- **Data Extracted**: `usage.total_tokens`, model name, input/output text, latency metrics, error codes. Integration via local HTTP with optional API key injection from `.env` (`ANTHROPIC_API_KEY`).
- **Reliability Enhancements**: Implement exponential backoff for 429/5xx responses and store raw requests in `.jsonl` files for reprocessing if Arize export is delayed.

### 4.2 OpenTelemetry Exporters (Arize AX & Phoenix)
- **Purpose**: Forward LiteLLM spans to hosted or local observability backends for visualization and downstream analytics.
- **Configuration**: Enabled through Docker Compose profiles with environment variables `ARIZE_API_KEY` and `ARIZE_SPACE_KEY` for cloud exports. See [observability backend setup](../README.md#2-choose-your-observability-backend). Phoenix is accessed via `http://localhost:6006`. ProdLens should provide connectors to fetch span data from these sources or, in Phoenix’s case, read from the local storage directory.
- **Usage in ProdLens**: Validate token usage and response status distributions; cross-reference with analyzer results to offer dashboards explaining correlation outcomes.
- **Operational Notes**: Configure batch export frequency (default: 60s) and retention (minimum 30 days for pilot) so that lagged analyses can rerun if GitHub data is delayed. Provide smoke tests that validate exporter reachability during installation.

### 4.3 GitHub REST API
- **Purpose**: Retrieve pull requests, commit activity, and rework signals (reopens) to compute DORA-aligned metrics.
- **Endpoints**:
  - `GET /repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc`
  - `GET /repos/{owner}/{repo}/commits?since=ISO8601`
  - Potentially `GET /repos/{owner}/{repo}/pulls/{pull_number}/events` for reopen detection if the `reopened_at` attribute is unavailable.
- **Caching Strategy**: Store ETags in SQLite; only refetch records when `updated_at` exceeds the last checkpoint. This lowers rate consumption and matches the MVP’s emphasis on a light-weight deployment.
- **Data Validation**: Apply schema checks on response payloads (e.g., ensure `merged_at` exists before calculating lead time) and log anomalies for manual review. When rate limits approach thresholds, fall back to GitHub’s GraphQL API for bulk queries to reduce request count.
- **Security**: Use `GITHUB_TOKEN` from `.env`, documented with the repo’s standard environment setup instructions. See the [environment setup checklist](../README.md#1-setup-environment).

### 4.4 CLI and SDK Integration Points
- **CLI**: `prod-lens report` command orchestrates ingestion, correlation, and output generation. It reads the same `.env` and respects `CLAUDE_LENS_PROXY_URL` if engineers route through remote proxies. See the [wrapper usage instructions](../README.md#3-use-claude-code).
- **Python SDK**: Example agents in `examples/python` can be extended with middleware to emit extra context (e.g., task labels, success flags) that ProdLens consumes to refine efficiency metrics. See the [examples guide](../README.md#quick-start-with-examples).
- **TypeScript SDK**: Similarly, wrappers around `examples/typescript` tasks supply additional metadata on accepted suggestions and session outcomes, making experience-sampling prompts more actionable.
- **Automation Hooks**: Provide a lightweight webhook listener (FastAPI) for agents that run outside of the proxy (e.g., CI bots). The listener standardizes payloads into the same schema used for CLI traces so that bots contribute to correlation analyses.

### 4.5 Optional Integrations
- **Arize Dashboards**: ProdLens should publish curated dashboards or saved views that highlight the computed metrics, bridging raw span data with analytic summaries.
- **Phoenix UI**: When teams choose local observability, provide a guide to correlate Phoenix traces with ProdLens’ CSV exports, possibly through tagging conventions (e.g., `attributes.prod_lens_session_id`).
- **Slack / Incident Tooling**: Integrate optional Slack webhooks that broadcast significant correlations or regressions, referencing the generated report artifacts.
- **Future Hooks**: Prepare minimal interfaces for A/B testing frameworks (v1.3 scope) by defining event schemas even if no experimentation engine is yet connected.

## 5. Additional Implementation Details

### 5.1 Data Pipeline Walkthrough
1. **Session Capture**: Developers run `claude-lens`, which proxies requests through LiteLLM. Each call produces JSONL logs and OpenTelemetry spans enriched with token counts and latency data.
2. **Trace Normalization**: A ProdLens ingestion job reads the JSONL or exported span data nightly, deriving per-session metrics (total tokens, accepted suggestion flag, estimated cost using Anthropic pricing tiers). Missing attributes (e.g., tool usage) are imputed with explicit “unknown” labels to avoid accidental data loss.
3. **GitHub Sync**: A scheduled task queries the GitHub API using cached checkpoints to gather merged PRs, commits, and detect reopen events within the past three weeks. Retries with conditional requests guarantee idempotency when runs overlap.
4. **Metric Aggregation**: Daily data frames join session aggregates with GitHub metrics. Lagged correlations compute AI activity vs. subsequent day outcomes, storing r/p values alongside effect-size translations (e.g., “+12% commits”). Confidence intervals accompany each statistic to signal estimation uncertainty.
5. **Reporting**: CLI renders a textual summary, writes CSV/JSON for further analysis, and optionally posts structured metrics to Arize/Phoenix for dashboarding. Reports include machine-readable metadata (Git commit, analyzer version) for auditability.
6. **Feedback Loop**: Experience-sampling prompts (should-have feature) are triggered randomly during sessions, with responses linked to the trace ID to study qualitative satisfaction vs. performance. Survey data is stored separately from code telemetry to simplify compliance reviews.

### 5.2 Pilot Execution Plan
- **Participant Setup**: Share a quick-start guide referencing the repository’s [Quick Start instructions](../README.md#quick-start) for choosing Arize or Phoenix telemetry and installing the `claude-lens` wrapper. Provide `.env.example` updates for ProdLens-specific secrets (GitHub token, analyzer configuration).
- **Operational Playbook**: Define a daily cron or GitHub Action that runs the analyzer script, stores outputs in a shared S3 bucket or Git repository, and posts highlights to Slack. Include dry-run support so new environments can validate configuration without consuming API quota.
- **Success Measurement**: After two weeks, review computed metrics vs. thresholds, confirm at least one significant AI-outcome association, and capture participant NPS and qualitative feedback.
- **Stakeholder Reviews**: Schedule midpoint and final readouts with engineering leadership, sharing dashboards and raw exports so results can be challenged and iterated quickly.

### 5.3 Risk Mitigation
- **Data Quality**: Lagged correlations require consistent timestamps; enforce UTC normalization when writing spans and GitHub data. Validate sample size daily to avoid false signals and flag low-sample metrics in reports.
- **Privacy**: Ensure traces do not capture sensitive code by leveraging LiteLLM’s existing privacy controls and providing documentation on safe usage. Offer optional redaction hooks before spans leave developer machines.
- **Scalability**: SQLite suffices for pilot scale, but abstract repository interfaces so migrations to Postgres or cloud data warehouses remain straightforward if adoption increases. Provide sizing guidance for when to graduate to managed databases.
- **API Limits**: With caching and delta fetches, GitHub requests stay under 100 calls/week, aligning with the MVP cost expectations.
- **Change Management**: Track configuration changes (e.g., switching observability profile) via version-controlled YAML to ensure reproducibility across pilot iterations.

### 5.4 Roadmap Considerations
- **v1.3 Targets**: Implement optional A/B testing scaffolding, expand rework detection with git blame diffing, and integrate SPACE framework surveys.
- **Extensibility**: Encourage contributions by documenting analyzer plugin interfaces (e.g., additional metrics) and aligning with open-source contribution guidelines.
- **Testing Strategy**: Leverage the provided SDK examples to generate deterministic traces, enabling regression tests for metric calculations without relying on live traffic.
- **Observability Enhancements**: Evaluate incorporating tracing-to-metric pipelines (e.g., OpenTelemetry Collector processors) to compute token histograms upstream, reducing load on the analyzer.

### 5.5 Documentation Deliverables
- Update repository docs with a `requirements.txt` for the analyzer, `.env.example` entries for ProdLens secrets, and a “Pilot Checklist” README section summarizing setup steps.
- Provide example output snippets (CLI + CSV) illustrating how significant associations are reported to stakeholders.
- Add troubleshooting guides for common proxy issues (e.g., LiteLLM health check failures, missing Arize credentials) referencing existing README instructions for restarting Docker profiles.
- Publish onboarding videos or step-by-step screenshots showing how to launch the proxy, run sample traces, and execute the analyzer, ensuring non-maintainers can self-serve.
- Maintain a decision log (ADR) capturing rationale for metric definitions, data sources, and future scope boundaries.

This design update aligns ProdLens MVP v1.2 with the concrete tooling in Dev-Agent-Lens, ensuring that the observability stack, ingestion scripts, and analytics pipeline interoperate smoothly during the pilot while leaving space for future experimentation enhancements.
