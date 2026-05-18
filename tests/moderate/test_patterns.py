"""Tests for PII pattern detection.

The patterns module exposes pure functions over text. These tests are
the contract for what counts as a PII hit vs. a false positive.
"""
from voc.moderate.patterns import scan_text


def test_scan_text_no_pii_returns_empty():
    assert scan_text("This is a bug report about a crash.") == []


def test_scan_text_detects_email():
    flags = scan_text("Contact me at alice@example.com for details")
    assert "email" in flags


def test_scan_text_email_with_subdomain():
    flags = scan_text("ping bob@mail.engineering.acme.org")
    assert "email" in flags


def test_scan_text_does_not_flag_github_handle_as_email():
    """@octocat is a GH handle, not PII in this context."""
    assert "email" not in scan_text("cc @octocat please review")


def test_scan_text_does_not_flag_word_at_word_without_dot():
    """foo@bar without a TLD is not an email match."""
    assert "email" not in scan_text("the foo@bar syntax in Python")


def test_scan_text_detects_us_phone_with_dashes():
    assert "phone" in scan_text("call me at 555-867-5309 thanks")


def test_scan_text_detects_us_phone_with_dots():
    assert "phone" in scan_text("phone: 555.867.5309")


def test_scan_text_detects_us_phone_with_parens():
    assert "phone" in scan_text("(555) 867-5309 is my number")


def test_scan_text_detects_us_phone_with_country_code():
    assert "phone" in scan_text("+1-555-867-5309")


def test_scan_text_does_not_flag_bare_10_digits_as_phone():
    """1234567890 with no separators is too ambiguous; do not flag."""
    assert "phone" not in scan_text("test id 1234567890 in the database")


def test_scan_text_does_not_flag_short_numbers():
    """Year-like 4-digit numbers should not trip phone detection."""
    assert "phone" not in scan_text("released in 2024 with patch 1.2.3")


def test_scan_text_detects_ssn_with_dashes():
    assert "ssn" in scan_text("SSN: 123-45-6789 on the form")


def test_scan_text_does_not_flag_short_id_as_ssn():
    """A 9-digit number without dash separators is not flagged as SSN."""
    assert "ssn" not in scan_text("issue id 123456789 was closed")


def test_scan_text_detects_credit_card_visa():
    """16-digit Visa-shaped number with valid prefix triggers cc flag."""
    flags = scan_text("card: 4532-1234-5678-9010")
    assert "credit_card" in flags


def test_scan_text_does_not_flag_random_16_digits():
    """Random 16-digit hex-like strings should not trigger cc."""
    flags = scan_text("hash: abc123def456 commit a1b2c3d4e5f6g7h8")
    assert "credit_card" not in flags


def test_scan_text_returns_unique_flags():
    """Multiple emails should result in one 'email' entry, not duplicates."""
    flags = scan_text("alice@a.com and bob@b.com both report")
    assert flags.count("email") == 1


def test_scan_text_returns_multiple_categories():
    """A text with email + phone returns both flags."""
    flags = scan_text("alice@example.com or call 555-867-5309")
    assert "email" in flags
    assert "phone" in flags
    assert len(flags) == 2


def test_scan_text_handles_empty_string():
    assert scan_text("") == []


def test_scan_text_handles_none_safe():
    """None input must not raise; treat as empty."""
    assert scan_text(None) == []
