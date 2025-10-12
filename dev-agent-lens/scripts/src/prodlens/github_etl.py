from __future__ import annotations

import datetime as dt
from typing import Dict, Optional

import requests

from .storage import ProdLensStore


def _parse_datetime(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    if isinstance(value, dt.datetime):
        return value.astimezone(dt.timezone.utc) if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    value = str(value)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc)


class GithubETL:
    """Synchronize GitHub pull request metadata into the ProdLens store."""

    def __init__(self, store: ProdLensStore, session: Optional[requests.Session] = None):
        self.store = store
        self.session = session or requests.Session()

    def _request(self, endpoint: str, params: Optional[Dict[str, object]] = None, token: Optional[str] = None):
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ProdLens-ETL",
        }
        etag = self.store.get_etag(endpoint)
        if etag:
            headers["If-None-Match"] = etag
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.session.get(url, headers=headers, params=params or {}, timeout=30)
        return response

    def sync_pull_requests(
        self,
        owner: str,
        repo: str,
        *,
        token: Optional[str] = None,
        since: Optional[dt.datetime] = None,
    ) -> int:
        endpoint = f"/repos/{owner}/{repo}/pulls"
        params = {
            "state": "closed",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
        }
        if since:
            params["since"] = since.astimezone(dt.timezone.utc).isoformat()

        response = self._request(endpoint, params=params, token=token)
        if response.status_code == 304:
            self.store.record_etl_run("pull_requests", 0, "Not modified")
            return 0
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

        etag = response.headers.get("ETag")
        if etag:
            self.store.set_etag(endpoint, etag)

        payload = response.json()
        if not isinstance(payload, list):
            return 0

        rows = []
        for item in payload:
            merged_at = _parse_datetime(item.get("merged_at"))
            created_at = _parse_datetime(item.get("created_at"))
            updated_at = _parse_datetime(item.get("updated_at"))
            reopened = bool(item.get("reopened_at"))
            rows.append(
                {
                    "id": item.get("id"),
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "author": (item.get("user") or {}).get("login"),
                    "state": item.get("state"),
                    "created_at": created_at,
                    "merged_at": merged_at,
                    "updated_at": updated_at,
                    "reopened": reopened,
                }
            )

        inserted = self.store.insert_pull_requests(rows)
        self.store.record_etl_run("pull_requests", inserted, f"Fetched {len(rows)} PRs")
        return inserted

    def sync_commits(
        self,
        owner: str,
        repo: str,
        *,
        token: Optional[str] = None,
        since: Optional[dt.datetime] = None,
    ) -> int:
        endpoint = f"/repos/{owner}/{repo}/commits"
        params = {"per_page": 100}
        if since:
            params["since"] = since.astimezone(dt.timezone.utc).isoformat()

        response = self._request(endpoint, params=params, token=token)
        if response.status_code == 304:
            self.store.record_etl_run("commits", 0, "Not modified")
            return 0
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

        etag = response.headers.get("ETag")
        if etag:
            self.store.set_etag(endpoint, etag)

        payload = response.json()
        if not isinstance(payload, list):
            return 0

        rows = []
        for item in payload:
            commit = item.get("commit", {}) or {}
            author_info = commit.get("author") or {}
            timestamp = _parse_datetime(author_info.get("date") or commit.get("committer", {}).get("date"))
            rows.append(
                {
                    "sha": item.get("sha"),
                    "author": author_info.get("name") or (item.get("author") or {}).get("login"),
                    "timestamp": timestamp,
                }
            )

        inserted = self.store.insert_commits(rows)
        self.store.record_etl_run("commits", inserted, f"Fetched {len(rows)} commits")
        return inserted
