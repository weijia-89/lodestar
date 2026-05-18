"""PII regex patterns + scanner.

The scanner is intentionally conservative: it would rather miss a real
PII hit than false-positive on common technical strings (hashes, IDs,
year numbers). False positives are the load-bearing failure mode here,
because every false positive creates reviewer fatigue and trains the
human to ignore the flag column.

Patterns and rationale:

- email: ASCII local-part `@` ASCII domain with a known TLD. We do NOT
  use `\\S+@\\S+` because that fires on `@octocat` references, code
  fragments like `foo@bar` (no TLD), and similar noise.
- phone: US format only for v0. Requires at least one of: dash, dot,
  paren separator. A bare 10-digit string (e.g., a database id) does
  NOT match. International formats are a known gap.
- ssn: US SSN format `NNN-NN-NNNN`. Requires dashes (a bare 9-digit
  string is too ambiguous).
- credit_card: 16-digit number with separator and a known card-prefix
  (4 for Visa, 5 for MC). We do NOT match bare 16-digit strings to
  avoid catching git SHAs and other hex-like noise.

Returns a list of category strings; duplicates collapsed.
"""
from __future__ import annotations

import re

# Known TLDs we treat as enough signal to call something an email.
# Deliberately a small allowlist; expand if real PII slips through.
_TLDS = (
    r"com|org|net|edu|gov|mil|io|co|us|uk|ca|au|de|fr|jp|cn|in|"
    r"info|biz|app|dev|tech|me"
)

_EMAIL_RE = re.compile(
    r"(?<![\w@])"  # not preceded by word char or @ (avoids ...@x@y matches)
    r"[a-zA-Z0-9._%+-]+"
    r"@"
    r"[a-zA-Z0-9.-]+\."
    rf"(?:{_TLDS})"
    r"\b",
)

# US phone: optional +1, then groups of 3-3-4 with dash/dot/paren separators
_PHONE_RE = re.compile(
    r"(?:\+?1[-.\s]?)?"  # optional country code
    r"(?:"
    r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}"  # (555) 867-5309
    r"|"
    r"\d{3}[-.]\d{3}[-.]\d{4}"  # 555-867-5309 or 555.867.5309
    r")",
)

# US SSN: NNN-NN-NNNN with required dashes
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Credit card: 4 or 5 prefix (Visa/MC), 16 digits in groups of 4
# separated by dash, space, or no separator (but at least one separator
# required so git SHAs do not match).
_CC_RE = re.compile(
    r"\b[45]\d{3}"
    r"[-\s]\d{4}"
    r"[-\s]\d{4}"
    r"[-\s]\d{4}\b",
)


def scan_text(text: str | None) -> list[str]:
    """Return a sorted list of unique PII category flags found in `text`.

    `None` and empty strings return [].
    """
    if not text:
        return []
    flags: set[str] = set()
    if _EMAIL_RE.search(text):
        flags.add("email")
    if _PHONE_RE.search(text):
        flags.add("phone")
    if _SSN_RE.search(text):
        flags.add("ssn")
    if _CC_RE.search(text):
        flags.add("credit_card")
    return sorted(flags)
