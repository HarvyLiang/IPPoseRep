"""Versioned experiment definitions and dependency-graph validation."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

_EXPERIMENT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class RegistryError(ValueError):
    """Raised when versioned experiment definitions are invalid."""


@dataclass(frozen=True, slots=True)
class ExperimentDefinition:
    """Validated experiment configuration loaded from TOML."""

    experiment_id: str
    description: str
    dependencies: tuple[str, ...]
    seed: int
    command: tuple[str, ...]
    dataset_manifest: Path
    metrics_file: Path
    required_artifacts: tuple[Path, ...]
    required_metrics: tuple[str, ...]
    source_path: Path
    config_sha256: str

    @classmethod
    def from_toml(cls, path: str | Path) -> ExperimentDefinition:
        source = Path(path).resolve()
        try:
            raw_bytes = source.read_bytes()
            data = tomllib.loads(raw_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise RegistryError(
                f"Cannot load experiment config {source}: {error}"
            ) from error

        experiment_id = _required_string(data, "id", source)
        if _EXPERIMENT_ID.fullmatch(experiment_id) is None:
            raise RegistryError(
                f"Invalid experiment id {experiment_id!r} in {source}; "
                "use lowercase letters, numbers, '_' or '-'"
            )

        description = _required_string(data, "description", source)
        dependencies = _string_list(
            data.get("dependencies", []),
            "dependencies",
            source,
            allow_empty=True,
        )
        if len(set(dependencies)) != len(dependencies):
            raise RegistryError(f"Duplicate dependencies in {source}")
        if experiment_id in dependencies:
            raise RegistryError(f"Experiment {experiment_id!r} depends on itself")

        seed = data.get("seed")
        if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
            raise RegistryError(f"seed must be a non-negative integer in {source}")

        command = _string_list(
            data.get("command", []), "command", source, allow_empty=True
        )
        dataset_manifest = _safe_relative_path(
            _required_string(data, "dataset_manifest", source),
            "dataset_manifest",
            source,
        )

        acceptance = data.get("acceptance")
        if not isinstance(acceptance, dict):
            raise RegistryError(f"[acceptance] table is required in {source}")
        metrics_file = _safe_relative_path(
            _required_string(acceptance, "metrics_file", source),
            "acceptance.metrics_file",
            source,
        )
        artifacts = tuple(
            _safe_relative_path(item, "acceptance.required_artifacts", source)
            for item in _string_list(
                acceptance.get("required_artifacts", []),
                "acceptance.required_artifacts",
                source,
                allow_empty=True,
            )
        )
        metrics = _string_list(
            acceptance.get("required_metrics", []),
            "acceptance.required_metrics",
            source,
        )
        if len(set(metrics)) != len(metrics):
            raise RegistryError(f"Duplicate required metrics in {source}")

        return cls(
            experiment_id=experiment_id,
            description=description,
            dependencies=tuple(dependencies),
            seed=seed,
            command=tuple(command),
            dataset_manifest=dataset_manifest,
            metrics_file=metrics_file,
            required_artifacts=artifacts,
            required_metrics=tuple(metrics),
            source_path=source,
            config_sha256=sha256(raw_bytes).hexdigest(),
        )


class ExperimentRegistry:
    """A validated collection of experiment definitions."""

    def __init__(self, definitions: list[ExperimentDefinition]) -> None:
        if not definitions:
            raise RegistryError("No experiment definitions were found")
        self._by_id: dict[str, ExperimentDefinition] = {}
        for definition in definitions:
            if definition.experiment_id in self._by_id:
                previous = self._by_id[definition.experiment_id]
                raise RegistryError(
                    f"Duplicate experiment id {definition.experiment_id!r}: "
                    f"{previous.source_path} and {definition.source_path}"
                )
            self._by_id[definition.experiment_id] = definition
        self._validate_dependencies()

    @classmethod
    def load(cls, config_root: str | Path) -> ExperimentRegistry:
        root = Path(config_root).resolve()
        if not root.is_dir():
            raise RegistryError(f"Experiment config directory does not exist: {root}")
        definitions = [
            ExperimentDefinition.from_toml(path)
            for path in sorted(root.rglob("*.toml"))
        ]
        return cls(definitions)

    def get(self, experiment_id: str) -> ExperimentDefinition:
        try:
            return self._by_id[experiment_id]
        except KeyError as error:
            available = ", ".join(sorted(self._by_id))
            raise RegistryError(
                f"Unknown experiment {experiment_id!r}; available: {available}"
            ) from error

    def definitions(self) -> tuple[ExperimentDefinition, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))

    def topological_order(self) -> tuple[str, ...]:
        order: list[str] = []
        visited: set[str] = set()

        def visit(experiment_id: str) -> None:
            if experiment_id in visited:
                return
            visited.add(experiment_id)
            for dependency in self._by_id[experiment_id].dependencies:
                visit(dependency)
            order.append(experiment_id)

        for experiment_id in sorted(self._by_id):
            visit(experiment_id)
        return tuple(order)

    def _validate_dependencies(self) -> None:
        for definition in self._by_id.values():
            missing = [
                dependency
                for dependency in definition.dependencies
                if dependency not in self._by_id
            ]
            if missing:
                raise RegistryError(
                    f"Experiment {definition.experiment_id!r} has missing "
                    f"dependencies: {', '.join(missing)}"
                )

        visiting: list[str] = []
        visited: set[str] = set()

        def visit(experiment_id: str) -> None:
            if experiment_id in visited:
                return
            if experiment_id in visiting:
                start = visiting.index(experiment_id)
                cycle = visiting[start:] + [experiment_id]
                raise RegistryError(
                    f"Experiment dependency cycle: {' -> '.join(cycle)}"
                )
            visiting.append(experiment_id)
            for dependency in self._by_id[experiment_id].dependencies:
                visit(dependency)
            visiting.pop()
            visited.add(experiment_id)

        for experiment_id in sorted(self._by_id):
            visit(experiment_id)


def _required_string(data: dict[str, object], key: str, source: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{key} must be a non-empty string in {source}")
    return value.strip()


def _string_list(
    value: object,
    field: str,
    source: Path,
    *,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise RegistryError(f"{field} must be a list of non-empty strings in {source}")
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        raise RegistryError(f"{field} must not be empty in {source}")
    return result


def _safe_relative_path(value: str, field: str, source: Path) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise RegistryError(f"{field} must be a safe relative path in {source}")
    return path
