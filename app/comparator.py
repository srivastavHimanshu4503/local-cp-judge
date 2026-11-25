from __future__ import annotations

from pathlib import Path
from typing import Iterator


def read_file_preview(path: Path, max_bytes: int = 500) -> str:
    """
    Reads at most max_bytes bytes from path (decoding UTF-8 with errors='replace'
    and normalizing CRLF to LF). If the file's total size exceeds max_bytes,
    appends '\n... [truncated, total size: {total_bytes / 1024:.1f} KB]'.
    """
    if not path.exists() or not path.is_file():
        return ""

    try:
        total_bytes = path.stat().st_size
        if total_bytes == 0:
            return ""

        with open(path, "rb") as f:
            raw_chunk = f.read(max_bytes)

        text = raw_chunk.decode("utf-8", errors="replace").replace("\r\n", "\n")
        if total_bytes > max_bytes:
            text += f"\n... [truncated, total size: {total_bytes / 1024:.1f} KB]"
        return text
    except Exception as e:
        return f"[Error reading preview: {e}]"


def streaming_lines(filepath: Path) -> Iterator[str]:
    """
    Streams stripped lines from filepath in O(1) memory.
    Strips trailing \r, \n, spaces, and tabs (line.rstrip('\r\n \t')).
    Buffers pending empty lines and only yields them if followed by a non-empty line,
    thereby ignoring trailing blank lines at EOF without buffering full files.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        pending_blanks = 0
        for raw_line in f:
            stripped = raw_line.rstrip("\r\n \t")
            if stripped == "":
                pending_blanks += 1
            else:
                while pending_blanks > 0:
                    yield ""
                    pending_blanks -= 1
                yield stripped


def compare_outputs(actual_path: Path, expected_path: Path) -> tuple[bool, str]:
    """
    Stream both files line-by-line in O(1) memory without reading full multi-MB files into memory.
    Normalizes Windows CRLF and Unix LF, strips trailing spaces/tabs per line, and ignores
    trailing blank lines at EOF in both files.

    Returns:
        (True, f"Matched {line_count} line(s)") on match, or
        (False, f"Mismatch at line {line_no}: expected '{exp_snip}', got '{act_snip}'")
        with snippets truncated to 80 characters.
    """
    if not actual_path.exists():
        return False, f"Actual output file does not exist: {actual_path.name}"
    if not expected_path.exists():
        return False, f"Expected answer file does not exist: {expected_path.name}"

    gen_act = streaming_lines(actual_path)
    gen_exp = streaming_lines(expected_path)

    line_count = 0
    while True:
        act_line = next(gen_act, None)
        exp_line = next(gen_exp, None)

        if act_line is None and exp_line is None:
            # Both streams completed and all non-empty lines matched
            return True, f"Matched {line_count} line(s)"

        line_count += 1

        if act_line != exp_line:
            if act_line is None:
                act_snip = "<EOF>"
            else:
                act_snip = act_line[:80] + "..." if len(act_line) > 80 else act_line

            if exp_line is None:
                exp_snip = "<EOF>"
            else:
                exp_snip = exp_line[:80] + "..." if len(exp_line) > 80 else exp_line

            return False, f"Mismatch at line {line_count}: expected '{exp_snip}', got '{act_snip}'"
