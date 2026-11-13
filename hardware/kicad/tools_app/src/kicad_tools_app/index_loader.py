"""Load and validate the checked-in executable allow-list."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import jsonschema


class IndexError(ValueError):
    """Raised when the module index is invalid or unsafe."""


class ModuleIndex:
    """Validated module definitions addressable only by stable ID."""

    def __init__(self, index_path: Path, schema_path: Path, repository_root: Path):
        """Validate index JSON, unique IDs, and static script boundaries."""
        try:
            document = json.loads(index_path.read_text(encoding="utf-8"))
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema).validate(document)
        except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
            raise IndexError(f"Invalid module index: {exc}") from exc
        self.document: dict[str, Any] = document
        self.repository_root = repository_root.resolve()
        self.app_dir = index_path.parent.resolve()
        self._modules: dict[str, dict[str, Any]] = {}
        modules_root = (self.repository_root / "modules").resolve()
        for module in document["modules"]:
            identifier = module["id"]
            if identifier in self._modules:
                raise IndexError(f"Duplicate module id: {identifier}")
            script = (self.app_dir / module["script"]).resolve()
            if not script.is_relative_to(modules_root) or not script.is_file():
                raise IndexError(f"Unsafe or missing script for {identifier}")
            stored = deepcopy(module)
            stored["resolved_script"] = str(script)
            self._modules[identifier] = stored

    @property
    def version(self) -> str:
        """Return the index schema version recorded with each run."""
        return str(self.document["schema_version"])

    def list_public(self) -> list[dict[str, Any]]:
        """Return enabled definitions without server-only resolved paths."""
        return [
            self._public(item) for item in self._modules.values() if item["enabled"]
        ]

    def get(self, module_id: str, *, require_enabled: bool = True) -> dict[str, Any]:
        """Return an indexed definition or raise ``KeyError`` when unavailable."""
        module = self._modules[module_id]
        if require_enabled and not module["enabled"]:
            raise KeyError(module_id)
        return deepcopy(module)

    def get_public(self, module_id: str) -> dict[str, Any]:
        """Return one enabled definition without its resolved script path."""
        return self._public(self.get(module_id))

    @staticmethod
    def _public(module: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(module)
        result.pop("resolved_script", None)
        result.pop("script", None)
        return result
