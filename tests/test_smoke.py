"""Smoke test: package imports cleanly."""
import voc


def test_version() -> None:
    assert voc.__version__ == "0.1.0"


def test_submodules_import() -> None:
    import voc.ingest  # noqa: F401
    import voc.dedup  # noqa: F401
    import voc.classify  # noqa: F401
    import voc.report  # noqa: F401
