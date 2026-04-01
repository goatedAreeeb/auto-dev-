"""Mock filesystem using a UnionFS-style base + overlay architecture."""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field


@dataclass
class MockFile:
    """Represents a single file in the mock filesystem."""

    path: str
    content: str = ""
    permissions: str = "rw-r--r--"
    is_readonly: bool = False


class MockFilesystem:
    """
    Dictionary-based layered filesystem.

    - **Base layer**: Read-only system files (e.g., /etc, /var).
    - **Write layer**: Mutable overlay where agent changes are stored.
    """

    def __init__(self) -> None:
        self._base: dict[str, MockFile] = {}
        self._overlay: dict[str, MockFile] = {}

    # ── Setup ───────────────────────────────────────────────────────

    def set_base(self, files: dict[str, MockFile]) -> None:
        """Load the immutable base layer (called once on task reset)."""
        self._base = {p: MockFile(path=p, content=f.content, permissions=f.permissions, is_readonly=True)
                      for p, f in files.items()}

    def set_overlay(self, files: dict[str, MockFile]) -> None:
        """Set initial overlay files (e.g., the broken state for a task)."""
        self._overlay = copy.deepcopy(files)

    def clear_overlay(self) -> None:
        """Wipe the write layer (used during reset)."""
        self._overlay.clear()

    # ── Read operations ─────────────────────────────────────────────

    def exists(self, path: str) -> bool:
        """Check if a file exists in the merged view."""
        return path in self._overlay or path in self._base

    def read(self, path: str) -> str:
        """Read file content from the merged view (overlay takes precedence)."""
        if path in self._overlay:
            return self._overlay[path].content
        if path in self._base:
            return self._base[path].content
        raise FileNotFoundError(f"No such file: {path}")

    def list_dir(self, dir_path: str) -> list[str]:
        """List children of a directory (merged view)."""
        dir_path = dir_path.rstrip("/") + "/"
        children: set[str] = set()
        for p in list(self._base.keys()) + list(self._overlay.keys()):
            if p.startswith(dir_path):
                relative = p[len(dir_path):]
                top = relative.split("/")[0]
                if top:
                    children.add(top)
        return sorted(children)

    def get_all_paths(self) -> list[str]:
        """Return all file paths in the merged view."""
        return sorted(set(list(self._base.keys()) + list(self._overlay.keys())))

    # ── Write operations ────────────────────────────────────────────

    def write(self, path: str, content: str) -> None:
        """Write or overwrite a file in the overlay layer."""
        self._overlay[path] = MockFile(path=path, content=content)

    def rename(self, src: str, dst: str) -> None:
        """Move / rename a file.  Works across both layers."""
        if src in self._overlay:
            file_obj = self._overlay.pop(src)
            file_obj.path = dst
            self._overlay[dst] = file_obj
        elif src in self._base:
            content = self._base[src].content
            self._overlay[dst] = MockFile(path=dst, content=content)
            # Mark the base file as "deleted" in the overlay
            self._overlay[src] = MockFile(path=src, content="__DELETED__")
        else:
            raise FileNotFoundError(f"No such file: {src}")

    def delete(self, path: str) -> None:
        """Delete a file from the overlay (or shadow a base file)."""
        if path in self._overlay:
            del self._overlay[path]
        elif path in self._base:
            self._overlay[path] = MockFile(path=path, content="__DELETED__")
        else:
            raise FileNotFoundError(f"No such file: {path}")

    # ── Snapshot ────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, str]:
        """Return a flat dict of path→content for the merged view."""
        merged: dict[str, str] = {}
        for p, f in self._base.items():
            merged[p] = f.content
        for p, f in self._overlay.items():
            if f.content == "__DELETED__":
                merged.pop(p, None)
            else:
                merged[p] = f.content
        return merged
