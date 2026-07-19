import unittest

from journal_factory.orchestrator_core.contracts import RunState
from journal_factory.orchestrator_core.errors import ErrorCode, OrchestratorError
from journal_factory.orchestrator_core.state_machine import RunStateMachine


class StateMachineTests(unittest.TestCase):
    def test_accepts_legal_pause_resume_and_completion_path(self) -> None:
        machine = RunStateMachine()

        for state in (
            RunState.VALIDATING,
            RunState.RUNNING,
            RunState.PAUSE_REQUESTED,
            RunState.PAUSED,
            RunState.RUNNING,
            RunState.COMPLETED,
        ):
            machine.transition(state)

        self.assertEqual(RunState.COMPLETED, machine.state)

    def test_rejects_illegal_transition_from_idle(self) -> None:
        machine = RunStateMachine()

        with self.assertRaises(OrchestratorError) as caught:
            machine.transition(RunState.COMPLETED)

        self.assertEqual(ErrorCode.RUN_TRANSITION_INVALID, caught.exception.code)
        self.assertEqual("idle", caught.exception.details["from_state"])


if __name__ == "__main__":
    unittest.main()
