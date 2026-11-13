"""Build explicit subprocess argument arrays from validated index values."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_command(
    module: dict[str, Any], values: dict[str, Any], python_executable: str
) -> list[str]:
    """Return a shell-free argument array containing no client-defined flags."""
    command = [str(Path(python_executable).resolve()), module["resolved_script"]]
    for parameter in module["parameters"]:
        name = parameter["name"]
        if name not in values:
            continue
        value = values[name]
        if parameter["kind"] == "positional":
            command.extend(_serialize(parameter, value))
        elif parameter["type"] == "boolean":
            if value:
                command.append(parameter["flag"])
        else:
            command.append(parameter["flag"])
            command.extend(_serialize(parameter, value))
    return command


def _serialize(parameter: dict[str, Any], value: Any) -> list[str]:
    if parameter["type"] == "string_list":
        return [str(item) for item in value]
    return [str(value)]
