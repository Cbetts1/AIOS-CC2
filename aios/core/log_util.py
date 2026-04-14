"""AI-OS log utility — shared JSONL append + single-generation rotation."""
import json
from pathlib import Path


def rotate_and_append(log_file: Path, entry: dict, rotate_bytes: int) -> None:
    """Append *entry* as a JSONL line to *log_file*.

    If the file already exceeds *rotate_bytes* it is first renamed to
    ``<stem>.1.jsonl`` (replacing any previous backup), then a fresh file is
    started.  Silently swallows all I/O errors so callers never crash due to
    logging failures.

    .. note::
        This is single-generation rotation.  A future upgrade to
        ``logging.handlers.RotatingFileHandler`` would provide multi-
        generation rotation; see README roadmap.
    """
    try:
        if log_file.exists() and log_file.stat().st_size > rotate_bytes:
            log_file.replace(log_file.with_suffix(".1.jsonl"))
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass
