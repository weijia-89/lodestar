"""Smoke test: package imports cleanly."""
import voc


def test_version() -> None:
    assert voc.__version__ == "0.1.0"


def test_submodules_import() -> None:
    import voc.classify
    import voc.dedup
    import voc.ingest
    import voc.report  # noqa: F401
