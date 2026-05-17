"""Disjoint-set / union-find with path compression. Shared by fuzzy + semantic dedup.

Determinism contract: union always merges the higher-id root into the lower-id root,
so cluster ids are stable for a given input order (= smallest member index per cluster).
"""
from __future__ import annotations


def find(parent: list[int], x: int) -> int:
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(parent: list[int], a: int, b: int) -> None:
    ra, rb = find(parent, a), find(parent, b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)
