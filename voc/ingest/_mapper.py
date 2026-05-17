"""Shared raw-GH-issue → Issue mapper. Per-tool wrappers pin repo + tool."""
import hashlib

from voc.schema.issue import Issue


def hash_login(login: str | None) -> str:
    """SHA-256 of GH login; '_anon' fallback for missing user."""
    if not login:
        login = "_anon"
    return hashlib.sha256(login.encode("utf-8")).hexdigest()


def map_raw(raw: dict, tool: str, repo: str) -> Issue:
    return Issue(
        id=f"{tool}:{raw['number']}",
        tool=tool,  # type: ignore[arg-type]
        repo=repo,
        number=raw["number"],
        title=raw["title"],
        body=raw.get("body") or "",
        url=raw["html_url"],
        state=raw["state"],
        created_at=raw["created_at"],
        updated_at=raw["updated_at"],
        closed_at=raw.get("closed_at"),
        labels=[label["name"] for label in (raw.get("labels") or [])],
        author_login_sha256=hash_login((raw.get("user") or {}).get("login")),
        comments_count=raw.get("comments", 0),
        reactions_count=(raw.get("reactions") or {}).get("total_count", 0),
    )
