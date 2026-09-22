from astra_journal.hermes.routing import HermesRouter
from astra_journal.hermes_client import HermesEndpoint, HermesError


class FakeClient:
    failures = {}

    def __init__(self, endpoint, **kwargs):
        self.endpoint = endpoint

    def chat_json(self, **kwargs):
        remaining = self.failures.get(self.endpoint.base_url, 0)
        if remaining:
            self.failures[self.endpoint.base_url] = remaining - 1
            raise HermesError("synthetic failure")
        return {"task": kwargs["task"]}, {"choices": []}, 0.01


def test_router_falls_back_after_main_failure() -> None:
    main = HermesEndpoint("http://main", "m", 1, "main")
    fallback = HermesEndpoint("http://fallback", "f", 1, "fallback")
    FakeClient.failures = {"http://main": 1, "http://fallback": 0}
    router = HermesRouter(
        [("main", main), ("fallback", fallback)],
        max_retries=0,
        retry_delay_s=0,
        client_factory=FakeClient,
    )
    result = router.chat_json(task="x", instruction="y")
    assert result.worker == "fallback"
