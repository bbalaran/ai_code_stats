from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import socket
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

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
    parser.add_argument("input", type=Path, help="Path to trace JSONL file (LiteLLM or Arize format)")
    parser.add_argument("--db", type=Path, default=Path(".prod-lens/cache.db"), help="Path to ProdLens SQLite cache")
    parser.add_argument("--repo", help="Repository slug (owner/name) applied to normalized records")
    parser.add_argument(
        "--format",
        type=str,
        choices=["litellm", "arize"],
        default="litellm",
        help="Trace format (default: litellm)",
    )
    parser.add_argument(
        "--dead-letter-dir",
        type=Path,
        default=Path(".prod-lens/dead-letter"),
        help="Directory for invalid payloads",
    )
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=Path(".prod-lens/parquet"),
        help="Directory for parquet cache output",
    )
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
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional CSV filepath for flattened metric output",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = create_parser()
    ns = parser.parse_args(argv)

    if ns.command == "ingest-traces":
        args = _create_ingest_traces_parser().parse_args(ns.args)
        with ProdLensStore(args.db) as store:
            ingestor = TraceIngestor(
                store,
                dead_letter_dir=args.dead_letter_dir,
                parquet_dir=args.parquet_dir,
            )
            inserted = ingestor.ingest_file(args.input, repo_slug=args.repo, format=args.format)
        print(f"✅ Ingested {inserted} trace records into {args.db}")
        return

    if ns.command == "ingest-github":
        args = _create_ingest_github_parser().parse_args(ns.args)
        token = args.token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise SystemExit("❌ GitHub token is required via --token or GITHUB_TOKEN")
        if "/" not in args.repo:
            raise SystemExit("❌ Repository must be in the format owner/name")
        owner, repo = args.repo.split("/", maxsplit=1)
        since = _parse_date(args.since) if args.since else None
        since_dt = dt.datetime.combine(since, dt.time.min, tzinfo=dt.timezone.utc) if since else None

        with ProdLensStore(args.db) as store:
            etl = GithubETL(store)
            inserted_prs = etl.sync_pull_requests(owner, repo, token=token, since=since_dt)
            inserted_commits = etl.sync_commits(owner, repo, token=token, since=since_dt)
        print(f"✅ Synced {inserted_prs} pull requests and {inserted_commits} commits into {args.db}")
        return

    if ns.command == "report":
        args = _create_report_parser().parse_args(ns.args)
        since = _parse_date(args.since)
        policy_models: Set[str] | None = set(args.policy_models) if args.policy_models else None

        with ProdLensStore(args.db) as store:
            generator = ReportGenerator(store)
            report = generator.generate_report(
                repo=args.repo,
                since=since,
                lag_days=args.lag_days,
                policy_models=policy_models,
            )
        report["metadata"]["runtime_profile"] = detect_runtime_profile()
        print_json(report)
        if args.output:
            rows = flatten_report(report)
            write_csv(args.output, rows)
            print(f"[INFO] Wrote CSV metrics to {args.output}")
        return

    parser.print_help()


def print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def detect_runtime_profile() -> Optional[str]:
    profiles = []
    if _port_is_open(4000):
        profiles.append("litellm-proxy")
    if _port_is_open(6006):
        profiles.append("phoenix-dashboard")
    if _port_is_open(8080):
        profiles.append("arize-exporter")
    return ", ".join(profiles) if profiles else None


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("localhost", port)) == 0


def flatten_report(report: Dict[str, object]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    def _walk(prefix: str, value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_prefix = f"{prefix}.{key}" if prefix else key
                _walk(key_prefix, nested)
        elif isinstance(value, list):
            rows.append({"metric": prefix, "value": json.dumps(value, default=str)})
        else:
            rows.append({"metric": prefix, "value": value})

    _walk("", report)
    return rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
