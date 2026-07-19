import unittest

from journal_factory.orchestrator_core.contracts import (
    CoreInvocationRequest,
    LLMTaskRequest,
)


class ContractTests(unittest.TestCase):
    def test_invocation_payload_is_defensively_copied_and_immutable(self) -> None:
        payload = {"article": {"id": "a-1"}, "values": [1, 2]}

        request = CoreInvocationRequest(
            request_id="run-1:core_a:1",
            run_id="run-1",
            core_id="core_a",
            operation="process",
            attempt=1,
            payload=payload,
        )
        payload["article"]["id"] = "changed"
        payload["values"].append(3)

        self.assertEqual("a-1", request.payload["article"]["id"])
        self.assertEqual((1, 2), request.payload["values"])
        with self.assertRaises(TypeError):
            request.payload["new"] = "not allowed"

    def test_llm_contract_is_structured_and_has_no_runtime_dependency(self) -> None:
        request = LLMTaskRequest(
            task_id="task-1",
            run_id="run-1",
            purpose="resolve ambiguity",
            evidence_references=("report:item-1",),
            constraints={"allowed": ["a", "b"]},
            response_schema={"type": "object"},
            minimum_confidence=0.8,
        )

        self.assertEqual(("report:item-1",), request.evidence_references)
        self.assertEqual(("a", "b"), request.constraints["allowed"])
        self.assertEqual(0.8, request.minimum_confidence)


if __name__ == "__main__":
    unittest.main()
