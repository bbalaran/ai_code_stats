from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
from typing import Iterable, Optional, Set

from .github_etl import GithubETL
from .metrics import ReportGenerator
from .storage import ProdLensStore
from .trace_ingestion import TraceIngestor


def _parse_date(value: str) -> dt.date:
    return dt.datetime.strptime(value, "%Y-%m-%d").date()


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ProdLens analytics toolkit built on top of Dev-Agent-Lens",
    )
    parser.add_argument("command", choices=["ingest-traces", "ingest-github", "report"], help="Operation to execute")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def _create_ingest_traces_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prod-lens ingest-traces")
    parser.add_argument("input", type=Path, help="Path to LiteLLM trace JSONL file")
    parser.add_argument("--db", type=Path, default=Path(".prod-lens/cache.db"), help="Path to ProdLens SQLite cache")
    return parser


def _create_ingest_github_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prod-lens ingest-github")
    parser.add_argument("--repo", required=True, help="Repository in the form owner/name")
    parser.add_argument("--token", help="GitHub token (defaults to GITHUB_TOKEN env variable)")
    parser.add_argument("--db", type=Path, default=Path(".prod-lens/cache.db"))
    parser.add_argument("--since", help="ISO date (YYYY-MM-DD) for incremental sync")
    return parser


def _create_report_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prod-lens report")
    parser.add_argument("--repo", required=True, help="Repository in the form owner/name")
    parser.add_argument("--db", type=Path, default=Path(".prod-lens/cache.db"))
    parser.add_argument("--since", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--lag-days", type=int, default=1, help="Lag days for AI-outcome correlation")
    parser.add_argument(
        "--policy-model",
        action="append",
        dest="policy_models",
        help="Model allowed by internal policy (repeatable)",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = create_parser()
    ns = parser.parse_args(argv)

    if ns.command == "ingest-traces":
        args = _create_ingest_traces_parser().parse_args(ns.args)
        store = ProdLensStore(args.db)
        ingestor = TraceIngestor(store)
        inserted = ingestor.ingest_file(args.input)
        print(f"✅ Ingested {inserted} trace records into {args.db}")
        return

    if ns.command == "ingest-github":
        args = _create_ingest_github_parser().parse_args(ns.args)
        token = args.token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise SystemExit("❌ GitHub token is required via --token or GITHUB_TOKEN")
        owner, repo = args.repo.split("/", maxsplit=1)
        since = _parse_date(args.since) if args.since else None
        since_dt = dt.datetime.combine(since, dt.time.min, tzinfo=dt.timezone.utc) if since else None

        store = ProdLensStore(args.db)
        etl = GithubETL(store)
        inserted_prs = etl.sync_pull_requests(owner, repo, token=token, since=since_dt)
        inserted_commits = etl.sync_commits(owner, repo, token=token, since=since_dt)
        print(f"✅ Synced {inserted_prs} pull requests and {inserted_commits} commits into {args.db}")
        return

    if ns.command == "report":
        args = _create_report_parser().parse_args(ns.args)
        since = _parse_date(args.since)
        policy_models: Set[str] | None = set(args.policy_models) if args.policy_models else None

        store = ProdLensStore(args.db)
        generator = ReportGenerator(store)
        report = generator.generate_report(
            repo=args.repo,
            since=since,
            lag_days=args.lag_days,
            policy_models=policy_models,
        )
        print_json(report)
        return

    parser.print_help()


def print_json(payload: dict) -> None:
    import json

    print(json.dumps(payload, indent=2, default=str))
