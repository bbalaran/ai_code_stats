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
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


class GithubETL:
    """Synchronize GitHub pull request metadata into the ProdLens store."""

    def __init__(self, store: ProdLensStore, session: Optional[requests.Session] = None):
        self.store = store
        self.session = session or requests.Session()

    def _cache_key(self, endpoint: str, params: Optional[Dict[str, object]]) -> str:
        if not params:
            return endpoint
        pairs = [
            f"{key}={params[key]}"
            for key in sorted(params)
            if key != "page" and params[key] is not None
        ]
        if not pairs:
            return endpoint
        return f"{endpoint}?{'&'.join(pairs)}"

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, object]] = None,
        token: Optional[str] = None,
        *,
        use_etag: bool = True,
        cache_key: Optional[str] = None,
    ):
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ProdLens-ETL",
        }
        key = cache_key or endpoint
        if use_etag:
            etag = self.store.get_etag(key)
            if etag:
                headers["If-None-Match"] = etag
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.session.get(url, headers=headers, params=params or {}, timeout=30)
        if use_etag and response.status_code < 400:
            etag_header = response.headers.get("ETag")
            if etag_header:
                self.store.set_etag(key, etag_header)
        return response

    @staticmethod
    def _has_next(response) -> bool:
        link_header = response.headers.get("Link")
        if not link_header:
            return False
        for part in link_header.split(","):
            if 'rel="next"' in part:
                return True
        return False

    def sync_pull_requests(
        self,
        owner: str,
        repo: str,
        *,
        token: Optional[str] = None,
        since: Optional[dt.datetime] = None,
    ) -> int:
        endpoint = f"/repos/{owner}/{repo}/pulls"
        base_params = {
            "state": "closed",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
        }
        if since:
            base_params["since"] = since.astimezone(dt.timezone.utc).isoformat()

        cache_key = self._cache_key(endpoint, base_params)

        rows = []
        page = 1
        while True:
            params = dict(base_params)
            params["page"] = page
            response = self._request(
                endpoint,
                params=params,
                token=token,
                use_etag=(page == 1),
                cache_key=cache_key,
            )

            if page == 1:
                if response.status_code == 304:
                    self.store.record_etl_run("pull_requests", 0, "Not modified")
                    return 0
                if response.status_code >= 400:
                    raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")
            else:
                if response.status_code >= 400:
                    raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

            payload = response.json()
            if not isinstance(payload, list) or not payload:
                break

            for item in payload:
                merged_at = _parse_datetime(item.get("merged_at"))
                created_at = _parse_datetime(item.get("created_at"))
                updated_at = _parse_datetime(item.get("updated_at"))
                reopened = False
                if merged_at:
                    reopened = self._was_reopened(owner, repo, item.get("number"), token=token)
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

            if not self._has_next(response):
                break
            page += 1

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
        base_params = {"per_page": 100}
        if since:
            base_params["since"] = since.astimezone(dt.timezone.utc).isoformat()

        cache_key = self._cache_key(endpoint, base_params)

        rows = []
        page = 1
        while True:
            params = dict(base_params)
            params["page"] = page
            response = self._request(
                endpoint,
                params=params,
                token=token,
                use_etag=(page == 1),
                cache_key=cache_key,
            )

            if page == 1:
                if response.status_code == 304:
                    self.store.record_etl_run("commits", 0, "Not modified")
                    return 0
                if response.status_code >= 400:
                    raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")
            else:
                if response.status_code >= 400:
                    raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

            payload = response.json()
            if not isinstance(payload, list) or not payload:
                break

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

            if not self._has_next(response):
                break
            page += 1

        inserted = self.store.insert_commits(rows)
        self.store.record_etl_run("commits", inserted, f"Fetched {len(rows)} commits")
        return inserted

    def _was_reopened(
        self,
        owner: str,
        repo: str,
        number: Optional[int],
        *,
        token: Optional[str] = None,
    ) -> bool:
        if not number:
            return False

        endpoint = f"/repos/{owner}/{repo}/issues/{number}/events"
        page = 1
        while True:
            response = self._request(
                endpoint,
                params={"per_page": 100, "page": page},
                token=token,
                use_etag=False,
            )
            if response.status_code >= 400:
                if response.status_code == 404:
                    return False
                raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

            payload = response.json()
            if isinstance(payload, list):
                for event in payload:
                    if isinstance(event, dict) and event.get("event") == "reopened":
                        return True
                if not payload:
                    break
            else:
                break

            if not self._has_next(response):
                break

            page += 1

        return False
