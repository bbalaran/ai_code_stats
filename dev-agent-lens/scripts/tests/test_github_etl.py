from pathlib import Path

import pytest

from prodlens.github_etl import GithubETL
from prodlens.storage import ProdLensStore


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or []
        self.headers = headers or {}
        self.text = ""

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
        FakeResponse(200, json_data=[]),
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

    assert len(session.calls) == 3
    first_headers = session.calls[0]["headers"]
    assert "If-None-Match" not in first_headers
    assert session.calls[1]["url"].endswith("/issues/10/events")
    second_headers = session.calls[2]["headers"]
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
                    }
                ],
                headers={"ETag": "etag"},
            ),
            FakeResponse(
                status_code,
                json_data=[
                    {"event": "closed"},
                    {"event": "reopened"},
                ],
            ),
        ]
    )
    etl = GithubETL(store, session=session)

    etl.sync_pull_requests("openai", "dev-agent-lens")

    rows = store.fetch_pull_requests()
    assert rows[0]["reopened"] is True


def test_github_etl_paginates_pull_requests(tmp_path: Path):
    store = ProdLensStore(tmp_path / "cache.db")
    responses = [
        FakeResponse(
            200,
            json_data=[
                {
                    "id": 11,
                    "number": 11,
                    "state": "closed",
                    "merged_at": "2024-01-02T10:00:00Z",
                    "created_at": "2024-01-01T09:30:00Z",
                    "updated_at": "2024-01-02T10:00:00Z",
                    "user": {"login": "dev-1"},
                    "title": "Add feature",
                }
            ],
            headers={
                "ETag": "etag-pr",
                "Link": '<https://api.github.com/repos/openai/dev-agent-lens/pulls?page=2>; rel="next"',
            },
        ),
        FakeResponse(200, json_data=[]),
        FakeResponse(
            200,
            json_data=[
                {
                    "id": 12,
                    "number": 12,
                    "state": "closed",
                    "merged_at": "2024-01-03T10:00:00Z",
                    "created_at": "2024-01-02T09:30:00Z",
                    "updated_at": "2024-01-03T10:00:00Z",
                    "user": {"login": "dev-2"},
                    "title": "Add more",
                }
            ],
        ),
        FakeResponse(200, json_data=[]),
    ]
    session = FakeSession(responses)
    etl = GithubETL(store, session=session)

    inserted = etl.sync_pull_requests("openai", "dev-agent-lens")

    assert inserted == 2
    assert len(store.fetch_pull_requests()) == 2
    assert session.calls[0]["params"]["page"] == 1
    assert session.calls[2]["params"]["page"] == 2
    assert "If-None-Match" not in session.calls[0]["headers"]
    assert "If-None-Match" not in session.calls[2]["headers"]


def test_github_etl_paginates_commits(tmp_path: Path):
    store = ProdLensStore(tmp_path / "cache.db")
    responses = [
        FakeResponse(
            200,
            json_data=[
                {
                    "sha": "abc",
                    "commit": {"author": {"name": "dev-1", "date": "2024-01-01T00:00:00Z"}},
                }
            ],
            headers={
                "ETag": "etag-commit",
                "Link": '<https://api.github.com/repos/openai/dev-agent-lens/commits?page=2>; rel="next"',
            },
        ),
        FakeResponse(
            200,
            json_data=[
                {
                    "sha": "def",
                    "commit": {"author": {"name": "dev-2", "date": "2024-01-02T00:00:00Z"}},
                }
            ],
        ),
    ]
    session = FakeSession(responses)
    etl = GithubETL(store, session=session)

    inserted = etl.sync_commits("openai", "dev-agent-lens")

    assert inserted == 2
    commits = store.fetch_commits()
    assert {row["sha"] for row in commits} == {"abc", "def"}
    assert session.calls[0]["params"]["page"] == 1
    assert session.calls[1]["params"]["page"] == 2
    assert "If-None-Match" not in session.calls[0]["headers"]
    assert "If-None-Match" not in session.calls[1]["headers"]
