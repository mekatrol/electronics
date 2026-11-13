"""Validate request values against index metadata and filesystem boundaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ParameterError(ValueError):
    """Raised when submitted module parameters violate the index contract."""


class ParameterValidator:
    """Strictly type-check and canonicalize module parameter values."""

    def __init__(self, allowed_roots: list[Path], repository_root: Path):
        """Create a validator constrained to existing canonical root paths."""
        self.allowed_roots = [root.resolve() for root in allowed_roots]
        self.repository_root = repository_root.resolve()

    def validate(
        self, module: dict[str, Any], submitted: dict[str, Any]
    ) -> dict[str, Any]:
        """Return normalized values or raise ``ParameterError`` before execution."""
        definitions = {item["name"]: item for item in module["parameters"]}
        unknown = sorted(set(submitted) - set(definitions))
        if unknown:
            raise ParameterError(f"Unknown parameters: {', '.join(unknown)}")
        values: dict[str, Any] = {}
        for name, definition in definitions.items():
            value = submitted.get(name, definition.get("default"))
            if value is None:
                if definition["required"]:
                    raise ParameterError(f"Missing required parameter: {name}")
                continue
            values[name] = self._validate_value(definition, value)
        return values

    def _validate_value(self, definition: dict[str, Any], value: Any) -> Any:
        name, kind = definition["name"], definition["type"]
        if kind == "boolean":
            if type(value) is not bool:
                raise ParameterError(f"{name} must be a boolean")
        elif kind == "integer":
            if type(value) is not int:
                raise ParameterError(f"{name} must be an integer")
        elif kind == "number":
            if type(value) not in (int, float):
                raise ParameterError(f"{name} must be a number")
        elif kind in ("string", "enum"):
            if not isinstance(value, str):
                raise ParameterError(f"{name} must be a string")
            if not value.strip():
                raise ParameterError(f"{name} must be a non-empty string")
        elif kind == "string_list":
            if not isinstance(value, list) or not all(
                isinstance(v, str) for v in value
            ):
                raise ParameterError(f"{name} must be a list of strings")
            if not value or any(not item.strip() for item in value):
                raise ParameterError(f"{name} must contain non-empty strings")
        elif kind in ("file", "directory"):
            return self._validate_path(definition, value)
        if "minimum" in definition and value < definition["minimum"]:
            raise ParameterError(f"{name} is below its minimum")
        if "maximum" in definition and value > definition["maximum"]:
            raise ParameterError(f"{name} exceeds its maximum")
        if "choices" in definition and value not in definition["choices"]:
            raise ParameterError(f"{name} is not an allowed choice")
        return value

    def _validate_path(self, definition: dict[str, Any], value: Any) -> str:
        name = definition["name"]
        if not isinstance(value, str) or not value.strip():
            raise ParameterError(f"{name} must be a non-empty path")
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = self.repository_root / candidate
        # strict=False resolves every existing parent symlink, preventing an escape
        # even for an output that is allowed to be created later.
        resolved = candidate.resolve(strict=False)
        if not any(resolved.is_relative_to(root) for root in self.allowed_roots):
            raise ParameterError(f"{name} is outside the allowed roots")
        extensions = definition.get("extensions", [])
        if extensions and resolved.suffix.lower() not in {
            e.lower() for e in extensions
        }:
            raise ParameterError(f"{name} has an unsupported extension")
        may_create = definition.get("may_create", False)
        if definition["type"] == "file":
            if not may_create and not resolved.is_file():
                raise ParameterError(f"{name} does not identify an existing file")
            if may_create and not resolved.parent.is_dir():
                resolved.parent.mkdir(parents=True, exist_ok=True)
        elif not resolved.is_dir():
            raise ParameterError(f"{name} does not identify an existing directory")
        return str(resolved)
