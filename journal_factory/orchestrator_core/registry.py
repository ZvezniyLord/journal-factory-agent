from __future__ import annotations

import re
from types import MappingProxyType
from typing import Mapping

from .contracts import CoreDescriptor
from .errors import ErrorCode, OrchestratorError
from .ports import CoreInvocationPort


CORE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_RETRIES = 10


class CoreRegistry:
    def __init__(self) -> None:
        self._descriptors: dict[str, CoreDescriptor] = {}
        self._ports: dict[str, CoreInvocationPort] = {}

    def register(self, descriptor: CoreDescriptor, port: CoreInvocationPort) -> None:
        if not CORE_ID_PATTERN.fullmatch(descriptor.core_id):
            raise OrchestratorError(
                ErrorCode.CORE_ID_INVALID,
                "Core ID must use lowercase ASCII letters, digits, and underscores.",
                {"core_id": descriptor.core_id},
            )
        if descriptor.core_id in self._descriptors:
            raise OrchestratorError(
                ErrorCode.CORE_ALREADY_REGISTERED,
                "Core ID is already registered.",
                {"core_id": descriptor.core_id},
            )
        if (
            isinstance(descriptor.max_retries, bool)
            or not isinstance(descriptor.max_retries, int)
            or not 0 <= descriptor.max_retries <= MAX_RETRIES
        ):
            raise OrchestratorError(
                ErrorCode.CORE_RETRY_LIMIT_INVALID,
                f"Retry limit must be an integer from 0 through {MAX_RETRIES}.",
                {"core_id": descriptor.core_id, "max_retries": descriptor.max_retries},
            )
        if descriptor.core_id in descriptor.dependencies:
            raise OrchestratorError(
                ErrorCode.CORE_DEPENDENCY_CYCLE,
                "A core cannot depend on itself.",
                {"core_id": descriptor.core_id},
            )
        self._descriptors[descriptor.core_id] = descriptor
        self._ports[descriptor.core_id] = port

    def has(self, core_id: str) -> bool:
        return core_id in self._descriptors

    @property
    def descriptors(self) -> Mapping[str, CoreDescriptor]:
        return MappingProxyType(dict(self._descriptors))

    def descriptor_for(self, core_id: str) -> CoreDescriptor:
        self._ensure_registered(core_id)
        return self._descriptors[core_id]

    def port_for(self, core_id: str) -> CoreInvocationPort:
        self._ensure_registered(core_id)
        return self._ports[core_id]

    def validate_dependencies(self) -> None:
        for core_id in sorted(self._descriptors):
            descriptor = self._descriptors[core_id]
            unknown = sorted(
                dependency
                for dependency in descriptor.dependencies
                if dependency not in self._descriptors
            )
            if unknown:
                raise OrchestratorError(
                    ErrorCode.CORE_DEPENDENCY_UNKNOWN,
                    "A registered core declares an unknown dependency.",
                    {"core_id": core_id, "dependencies": unknown},
                )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(core_id: str, path: tuple[str, ...]) -> None:
            if core_id in visiting:
                cycle_start = path.index(core_id)
                cycle = path[cycle_start:] + (core_id,)
                raise OrchestratorError(
                    ErrorCode.CORE_DEPENDENCY_CYCLE,
                    "Core dependency graph contains a cycle.",
                    {"cycle": list(cycle)},
                )
            if core_id in visited:
                return
            visiting.add(core_id)
            for dependency in sorted(self._descriptors[core_id].dependencies):
                visit(dependency, path + (core_id,))
            visiting.remove(core_id)
            visited.add(core_id)

        for core_id in sorted(self._descriptors):
            visit(core_id, ())

    def validate_pipeline(
        self,
        pipeline: tuple[str, ...],
        pre_satisfied_dependencies: frozenset[str],
    ) -> None:
        if not pipeline:
            raise OrchestratorError(
                ErrorCode.PIPELINE_EMPTY,
                "Pipeline must contain at least one core.",
            )
        if len(set(pipeline)) != len(pipeline):
            raise OrchestratorError(
                ErrorCode.PIPELINE_CORE_DUPLICATE,
                "Pipeline cannot invoke the same core more than once.",
                {"pipeline": list(pipeline)},
            )
        for core_id in pipeline:
            self._ensure_registered(core_id)

        self.validate_dependencies()
        satisfied = set(pre_satisfied_dependencies)
        for core_id in pipeline:
            descriptor = self._descriptors[core_id]
            missing = sorted(
                dependency
                for dependency in descriptor.dependencies
                if dependency not in satisfied
            )
            if missing:
                raise OrchestratorError(
                    ErrorCode.PIPELINE_DEPENDENCY_UNSATISFIED,
                    "Pipeline places a core before a required dependency.",
                    {"core_id": core_id, "dependencies": missing},
                )
            satisfied.add(core_id)

    def _ensure_registered(self, core_id: str) -> None:
        if core_id not in self._descriptors:
            raise OrchestratorError(
                ErrorCode.CORE_NOT_REGISTERED,
                "Core is not registered.",
                {"core_id": core_id},
            )
