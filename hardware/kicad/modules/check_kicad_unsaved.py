#!/usr/bin/env python3
"""Report whether an open PCB differs from its saved file through KiCad IPC."""

from __future__ import annotations

import sys
from pathlib import Path

from kipy import KiCad
from kipy.board import Board
from kipy.proto.common.types import DocumentType

from kicad_ipc import board_document_path, board_has_unsaved_changes


def main() -> int:
    """Return 2 when the requested open board has changes not present on disk."""
    target = Path(sys.argv[1]).resolve()
    try:
        client = KiCad(timeout_ms=1500)
        documents = client.get_open_documents(DocumentType.DOCTYPE_PCB)
        for document in documents:
            if board_document_path(document) != target:
                continue
            board = Board(client._client, document)
            return 2 if board_has_unsaved_changes(board, target) else 0
    except Exception:
        # IPC is an optional enhancement. The caller retains its filesystem
        # autosave check when KiCad is closed, busy, or otherwise unavailable.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
