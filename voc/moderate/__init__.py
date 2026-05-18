"""PII / moderation flagging for the lodestar pipeline.

Regex-based first-pass scan over Issue title + body. Adds a `pii_flags`
column to the parquet but never redacts or drops rows. Reviewer decides
disposition.

Per AGENTS.md refusal list: LLM-based moderation is NOT load-bearing.
Regex is the load-bearing layer. An LLM augmentation layer could be
added later but must not replace this module's contract.
"""
