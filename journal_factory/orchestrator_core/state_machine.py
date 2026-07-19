from __future__ import annotations

from .contracts import RunState
from .errors import ErrorCode, OrchestratorError


ALLOWED_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.IDLE: frozenset({RunState.VALIDATING}),
    RunState.VALIDATING: frozenset({RunState.RUNNING, RunState.FAILED}),
    RunState.RUNNING: frozenset(
        {
            RunState.PAUSE_REQUESTED,
            RunState.PAUSED,
            RunState.COMPLETED,
            RunState.COMPLETED_WITH_WARNINGS,
            RunState.FAILED,
        }
    ),
    RunState.PAUSE_REQUESTED: frozenset({RunState.PAUSED}),
    RunState.PAUSED: frozenset({RunState.RUNNING, RunState.FAILED}),
    RunState.COMPLETED: frozenset(),
    RunState.COMPLETED_WITH_WARNINGS: frozenset(),
    RunState.FAILED: frozenset(),
}


class RunStateMachine:
    def __init__(self) -> None:
        self._state = RunState.IDLE

    @property
    def state(self) -> RunState:
        return self._state

    def transition(self, target: RunState) -> None:
        if target not in ALLOWED_TRANSITIONS[self._state]:
            raise OrchestratorError(
                ErrorCode.RUN_TRANSITION_INVALID,
                "Run state transition is not permitted.",
                {"from_state": self._state.value, "to_state": target.value},
            )
        self._state = target
