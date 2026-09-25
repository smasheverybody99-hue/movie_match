"""Small helpers shared by the pipeline command lines."""

import re
import sys
from pathlib import Path

# A Markdown table row whose first cell is a TMDB id: "| 550 | Fight Club | ..."
_TABLE_ROW = re.compile(r"^\s*\|\s*(\d+)\s*\|")


def read_ids(arg: str) -> list[int]:
    """TMDB ids from "550,680 13" or from a file such as docs/review-films.md.

    In a file, ids are read from the first column of Markdown table rows, so the list
    can carry titles and notes for the person reviewing it. Order is kept; repeats are
    dropped.
    """
    path = Path(arg)
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        found = [int(m.group(1)) for line in lines if (m := _TABLE_ROW.match(line))]
        source = str(path)
    else:
        tokens = [t for t in re.split(r"[,\s]+", arg.strip()) if t]
        bad = [t for t in tokens if not t.isdigit()]
        if bad:
            raise ValueError(f"not a TMDB id or an existing file: {', '.join(bad)}")
        found = [int(t) for t in tokens]
        source = "the command line"
    ids = list(dict.fromkeys(found))
    if not ids:
        raise ValueError(f"no TMDB ids found in {source}")
    return ids


def utf8_console() -> None:
    """Print film titles safely on a Windows console (often cp1251/cp1252).

    Without this, the first title with a character the code page lacks - "Amélie" -
    raises UnicodeEncodeError and kills the command.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
