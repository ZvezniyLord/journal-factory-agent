from __future__ import annotations

from typing import Any, Mapping

from .contracts import (
    ActionRecord,
    CoreInvocationRequest,
    CoreInvocationResult,
    FailureRoute,
    InvocationError,
    InvocationStatus,
    PauseRequest,
    ResumeRequest,
    RunRequest,
    RunSnapshot,
    RunState,
)
from .errors import ErrorCode, OrchestratorError
from .ports import ActionLogPort, ClockPort
from .registry import CoreRegistry
from .state_machine import RunStateMachine


class Orchestrator:
    def __init__(
        self,
        registry: CoreRegistry,
        action_log: ActionLogPort,
        clock: ClockPort,
    ) -> None:
        self._registry = registry
        self._action_log = action_log
        self._clock = clock
        self._machine = RunStateMachine()
        self._request: RunRequest | None = None
        self._cursor = 0
        self._current_core: str | None = None
        self._completed: list[str] = []
        self._attempts: dict[str, int] = {}
        self._warnings: list[InvocationError] = []
        self._failure: InvocationError | None = None
        self._pause_reason: str | None = None
        self._revision = 0
        self._action_count = 0

    def begin(self, request: RunRequest) -> RunSnapshot:
        if self._machine.state is not RunState.IDLE:
            raise OrchestratorError(
                ErrorCode.RUN_ALREADY_ACTIVE,
                "This Orchestrator instance already owns a run.",
                {"state": self._machine.state.value},
            )
        if not isinstance(request.run_id, str) or not request.run_id.strip():
            raise OrchestratorError(
                ErrorCode.RUN_ID_INVALID,
                "Run ID must be a non-empty string.",
            )

        self._request = request
        self._transition(RunState.VALIDATING, "Pipeline validation started.")
        try:
            self._registry.validate_pipeline(
                request.pipeline, request.pre_satisfied_dependencies
            )
        except OrchestratorError as error:
            self._failure = InvocationError(
                error.code.value,
                error.message,
                False,
                error.details,
            )
            self._record(
                action="pipeline_validation",
                status="failed",
                message=error.message,
                details={"error_code": error.code.value},
            )
            self._transition(RunState.FAILED, "Pipeline validation failed.")
            raise

        self._record(
            action="pipeline_validation",
            status="success",
            message="Pipeline dependencies and order are valid.",
            details={"pipeline": list(request.pipeline)},
        )
        self._transition(RunState.RUNNING, "Run is ready for core invocation.")
        return self.snapshot()

    def advance(self) -> RunSnapshot:
        self._require_run()
        if self._machine.state is RunState.PAUSE_REQUESTED:
            self._transition(RunState.PAUSED, "Pause acknowledged before invocation.")
            self._record(
                action="pause_acknowledged",
                status="success",
                message="Run paused between core invocations.",
            )
            return self.snapshot()
        if self._machine.state is not RunState.RUNNING:
            self._raise_transition_error(RunState.RUNNING)

        assert self._request is not None
        if self._cursor >= len(self._request.pipeline):
            self._finalize()
            return self.snapshot()

        core_id = self._request.pipeline[self._cursor]
        descriptor = self._registry.descriptor_for(core_id)
        port = self._registry.port_for(core_id)
        payload = self._request.payload_by_core.get(core_id, {})
        self._current_core = core_id
        base_attempt = self._attempts.get(core_id, 0)

        for offset in range(1, descriptor.max_retries + 2):
            attempt = base_attempt + offset
            self._attempts[core_id] = attempt
            invocation = CoreInvocationRequest(
                request_id=f"{self._request.run_id}:{core_id}:{attempt}",
                run_id=self._request.run_id,
                core_id=core_id,
                operation=descriptor.operation,
                attempt=attempt,
                payload=payload,
            )
            self._record(
                action="core_invocation",
                status="started",
                core_id=core_id,
                attempt=attempt,
                message="Core invocation started.",
                details={"request_id": invocation.request_id},
            )
            result = self._invoke_safely(port, invocation)

            if result.status is InvocationStatus.SUCCESS:
                self._completed.append(core_id)
                self._cursor += 1
                self._current_core = None
                self._record(
                    action="core_invocation",
                    status="success",
                    core_id=core_id,
                    attempt=attempt,
                    message="Core invocation succeeded.",
                    details={"output_keys": sorted(result.output)},
                )
                if self._cursor >= len(self._request.pipeline):
                    self._finalize()
                return self.snapshot()

            assert result.error is not None
            can_retry = (
                result.status is InvocationStatus.RETRYABLE_FAILURE
                and offset <= descriptor.max_retries
            )
            if can_retry:
                self._record(
                    action="retry_scheduled",
                    status="warning",
                    core_id=core_id,
                    attempt=attempt,
                    message="Retryable failure will be retried.",
                    details={"error_code": result.error.code},
                )
                continue

            self._route_failure(descriptor.failure_route, core_id, attempt, result.error)
            return self.snapshot()

        raise AssertionError("bounded retry loop must always return")

    def request_pause(self, request: PauseRequest) -> RunSnapshot:
        self._require_matching_run(request.run_id)
        if self._machine.state is not RunState.RUNNING:
            self._raise_transition_error(RunState.PAUSE_REQUESTED)
        self._pause_reason = request.reason.strip() or "Pause requested."
        self._transition(RunState.PAUSE_REQUESTED, "Pause requested.")
        return self.snapshot()

    def resume(self, request: ResumeRequest) -> RunSnapshot:
        self._require_matching_run(request.run_id)
        if self._machine.state is not RunState.PAUSED:
            raise OrchestratorError(
                ErrorCode.RUN_NOT_PAUSED,
                "Run can be resumed only from paused state.",
                {"state": self._machine.state.value},
            )
        self._pause_reason = None
        self._failure = None
        self._transition(RunState.RUNNING, "Paused run resumed.")
        return self.snapshot()

    def run_to_terminal(self) -> RunSnapshot:
        while self._machine.state in {RunState.RUNNING, RunState.PAUSE_REQUESTED}:
            snapshot = self.advance()
            if snapshot.state is RunState.PAUSED:
                break
        return self.snapshot()

    def snapshot(self) -> RunSnapshot:
        pipeline = self._request.pipeline if self._request else ()
        next_core = pipeline[self._cursor] if self._cursor < len(pipeline) else None
        return RunSnapshot(
            run_id=self._request.run_id if self._request else None,
            state=self._machine.state,
            pipeline=pipeline,
            current_core=self._current_core,
            next_core=next_core,
            completed_cores=tuple(self._completed),
            attempts=self._attempts,
            warnings=tuple(self._warnings),
            failure=self._failure,
            pause_reason=self._pause_reason,
            revision=self._revision,
            action_count=self._action_count,
        )

    def _invoke_safely(self, port, request: CoreInvocationRequest) -> CoreInvocationResult:
        try:
            result = port.invoke(request)
        except Exception:
            return CoreInvocationResult.terminal_failure(
                "CORE_INVOCATION_EXCEPTION",
                "Core adapter raised an exception; private details were suppressed.",
            )
        if not isinstance(result, CoreInvocationResult):
            return CoreInvocationResult.terminal_failure(
                ErrorCode.CORE_RESULT_INVALID.value,
                "Core adapter returned a value outside the invocation contract.",
            )
        return result

    def _route_failure(
        self,
        route: FailureRoute,
        core_id: str,
        attempt: int,
        error: InvocationError,
    ) -> None:
        self._record(
            action="core_invocation",
            status="failed",
            core_id=core_id,
            attempt=attempt,
            message="Core invocation failed.",
            details={"error_code": error.code, "failure_route": route.value},
        )
        if route is FailureRoute.FAIL_RUN:
            self._failure = error
            self._transition(RunState.FAILED, "Failure route stopped the run.")
            return
        if route is FailureRoute.PAUSE_RUN:
            self._failure = error
            self._pause_reason = error.message
            self._transition(RunState.PAUSED, "Failure route paused the run.")
            return

        self._warnings.append(error)
        self._completed.append(core_id)
        self._cursor += 1
        self._current_core = None
        self._record(
            action="failure_routed",
            status="warning",
            core_id=core_id,
            attempt=attempt,
            message="Failure recorded as warning; pipeline will continue.",
            details={"error_code": error.code},
        )
        assert self._request is not None
        if self._cursor >= len(self._request.pipeline):
            self._finalize()

    def _finalize(self) -> None:
        target = (
            RunState.COMPLETED_WITH_WARNINGS
            if self._warnings
            else RunState.COMPLETED
        )
        self._current_core = None
        self._transition(target, "Pipeline reached a terminal success state.")

    def _transition(self, target: RunState, message: str) -> None:
        previous = self._machine.state
        self._machine.transition(target)
        self._record(
            action="state_transition",
            status="success",
            message=message,
            details={"from_state": previous.value, "to_state": target.value},
        )

    def _record(
        self,
        *,
        action: str,
        status: str,
        message: str,
        core_id: str | None = None,
        attempt: int | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        timestamp = self._clock.now().isoformat().replace("+00:00", "Z")
        record = ActionRecord(
            sequence=self._action_count + 1,
            timestamp_utc=timestamp,
            run_id=self._request.run_id if self._request else None,
            core_id=core_id,
            action=action,
            status=status,
            attempt=attempt,
            message=message,
            details=details or {},
        )
        try:
            self._action_log.append(record)
        except Exception as error:
            raise OrchestratorError(
                ErrorCode.ACTION_LOG_WRITE_FAILED,
                "Action log adapter rejected an append operation.",
                {"action": action},
            ) from error
        self._action_count += 1
        self._revision += 1

    def _require_run(self) -> None:
        if self._request is None:
            raise OrchestratorError(
                ErrorCode.RUN_NOT_FOUND,
                "No run has been started in this Orchestrator instance.",
            )

    def _require_matching_run(self, run_id: str) -> None:
        self._require_run()
        assert self._request is not None
        if run_id != self._request.run_id:
            raise OrchestratorError(
                ErrorCode.RUN_ID_MISMATCH,
                "Command run ID does not match the active run.",
                {"requested_run_id": run_id, "active_run_id": self._request.run_id},
            )

    def _raise_transition_error(self, requested_state: RunState) -> None:
        raise OrchestratorError(
            ErrorCode.RUN_TRANSITION_INVALID,
            "Command is not legal in the current run state.",
            {
                "state": self._machine.state.value,
                "requested_state": requested_state.value,
            },
        )
