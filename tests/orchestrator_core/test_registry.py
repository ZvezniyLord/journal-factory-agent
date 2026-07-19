import unittest

from journal_factory.orchestrator_core.contracts import CoreDescriptor
from journal_factory.orchestrator_core.errors import ErrorCode, OrchestratorError
from journal_factory.orchestrator_core.registry import CoreRegistry


class NoOpCore:
    def invoke(self, request):
        raise AssertionError("not called by registry tests")


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = CoreRegistry()
        self.port = NoOpCore()

    def assert_error(self, code: ErrorCode, callback) -> None:
        with self.assertRaises(OrchestratorError) as caught:
            callback()
        self.assertEqual(code, caught.exception.code)

    def test_registers_a_core_and_rejects_duplicate_id(self) -> None:
        self.registry.register(CoreDescriptor("core_a"), self.port)

        self.assertTrue(self.registry.has("core_a"))
        self.assert_error(
            ErrorCode.CORE_ALREADY_REGISTERED,
            lambda: self.registry.register(CoreDescriptor("core_a"), self.port),
        )

    def test_rejects_invalid_id_and_retry_limit(self) -> None:
        self.assert_error(
            ErrorCode.CORE_ID_INVALID,
            lambda: self.registry.register(CoreDescriptor("Core A"), self.port),
        )
        self.assert_error(
            ErrorCode.CORE_RETRY_LIMIT_INVALID,
            lambda: self.registry.register(
                CoreDescriptor("core_a", max_retries=-1), self.port
            ),
        )

    def test_rejects_unknown_and_cyclic_dependencies(self) -> None:
        self.registry.register(
            CoreDescriptor("core_a", dependencies=("missing",)), self.port
        )
        self.assert_error(
            ErrorCode.CORE_DEPENDENCY_UNKNOWN,
            self.registry.validate_dependencies,
        )

        cyclic = CoreRegistry()
        cyclic.register(CoreDescriptor("core_a", dependencies=("core_b",)), self.port)
        cyclic.register(CoreDescriptor("core_b", dependencies=("core_a",)), self.port)
        self.assert_error(
            ErrorCode.CORE_DEPENDENCY_CYCLE,
            cyclic.validate_dependencies,
        )

    def test_validates_pipeline_order_and_pre_satisfied_dependencies(self) -> None:
        self.registry.register(CoreDescriptor("workspace"), self.port)
        self.registry.register(
            CoreDescriptor("article", dependencies=("workspace",)), self.port
        )

        self.registry.validate_pipeline(("workspace", "article"), frozenset())
        self.registry.validate_pipeline(("article",), frozenset({"workspace"}))
        self.assert_error(
            ErrorCode.PIPELINE_DEPENDENCY_UNSATISFIED,
            lambda: self.registry.validate_pipeline(
                ("article", "workspace"), frozenset()
            ),
        )

    def test_rejects_empty_duplicate_and_unregistered_pipeline_cores(self) -> None:
        self.registry.register(CoreDescriptor("core_a"), self.port)

        self.assert_error(
            ErrorCode.PIPELINE_EMPTY,
            lambda: self.registry.validate_pipeline((), frozenset()),
        )
        self.assert_error(
            ErrorCode.PIPELINE_CORE_DUPLICATE,
            lambda: self.registry.validate_pipeline(
                ("core_a", "core_a"), frozenset()
            ),
        )
        self.assert_error(
            ErrorCode.CORE_NOT_REGISTERED,
            lambda: self.registry.validate_pipeline(("missing",), frozenset()),
        )


if __name__ == "__main__":
    unittest.main()
