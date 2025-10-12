from pathlib import Path

import pytest

from prodlens.github_etl import GithubETL
from prodlens.storage import ProdLensStore


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or []
        self.headers = headers or {}

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params or {}})
        if not self.responses:
            raise AssertionError("No more fake responses configured")
        return self.responses.pop(0)


def test_github_etl_uses_etags_and_persists_data(tmp_path: Path):
    store = ProdLensStore(tmp_path / "cache.db")
    responses = [
        FakeResponse(
            200,
            json_data=[
                {
                    "id": 1,
                    "number": 10,
                    "state": "closed",
                    "merged_at": "2024-01-02T10:00:00Z",
                    "created_at": "2024-01-01T09:30:00Z",
                    "updated_at": "2024-01-02T10:00:00Z",
                    "user": {"login": "dev-1"},
                    "head": {"ref": "main"},
                    "base": {"ref": "main"},
                    "rebaseable": True,
                    "draft": False,
                    "title": "Add feature",
                }
            ],
            headers={"ETag": "etag-pr"},
        ),
        FakeResponse(304, headers={"ETag": "etag-pr"}),
    ]

    session = FakeSession(responses)
    etl = GithubETL(store, session=session)

    inserted = etl.sync_pull_requests("openai", "dev-agent-lens")
    assert inserted == 1

    rows = store.fetch_pull_requests()
    assert len(rows) == 1
    assert rows[0]["number"] == 10

    inserted_second = etl.sync_pull_requests("openai", "dev-agent-lens")
    assert inserted_second == 0

    assert len(session.calls) == 2
    first_headers = session.calls[0]["headers"]
    assert "If-None-Match" not in first_headers
    second_headers = session.calls[1]["headers"]
    assert second_headers.get("If-None-Match") == "etag-pr"


@pytest.mark.parametrize("status_code", [200, 201, 202])
def test_github_etl_classifies_reopened(status_code, tmp_path: Path):
    store = ProdLensStore(tmp_path / "cache.db")
    session = FakeSession(
        [
            FakeResponse(
                200,
                json_data=[
                    {
                        "id": 2,
                        "number": 5,
                        "state": "closed",
                        "merged_at": "2024-01-05T11:00:00Z",
                        "created_at": "2024-01-04T08:00:00Z",
                        "updated_at": "2024-01-05T12:00:00Z",
                        "user": {"login": "dev-2"},
                        "title": "Bug fix",
                        "head": {"ref": "bugfix"},
                        "base": {"ref": "main"},
                        "draft": False,
                        "rebaseable": True,
                        "reopened_at": "2024-01-05T10:30:00Z",
                    }
                ],
                headers={"ETag": "etag"},
            )
        ]
    )
    etl = GithubETL(store, session=session)

    etl.sync_pull_requests("openai", "dev-agent-lens")

    rows = store.fetch_pull_requests()
    assert rows[0]["reopened"] is True
