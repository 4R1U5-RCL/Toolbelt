"""Delivery verification: the difference between accepted and delivered."""

import json
import unittest

import helpers  # noqa: F401  (path setup)
from helpers import FakeClock, FakeResolver, RecordingClient, ok

from telegram.http import HttpTransient
from telegram.verify import DeliveryVerifier, Verdict

WIRED = {"N8N_BASE_URL": "https://n8n.test", "N8N_API_KEY": "key-abcdef123456"}


def listing(*ids):
    return ok(json.dumps({"data": [{"id": i} for i in ids]}).encode("utf-8"))


def execution(exec_id, nodes, request_id="req-1"):
    """One execution record, shaped like n8n's `includeData=true` response."""
    return ok(json.dumps({
        "id": exec_id,
        "data": {"resultData": {
            "runData": {name: [{"error": err} if err else {"data": {}}]
                        for name, err in nodes.items()},
            "lastNodeExecuted": "Respond",
        }},
        "body": {"request_id": request_id},
    }).encode("utf-8"))


def verifier(responses, values=None):
    return DeliveryVerifier(FakeResolver(values if values is not None else WIRED),
                            client=RecordingClient(responses), clock=FakeClock())


class TestAvailability(unittest.TestCase):
    def test_unconfigured_is_unavailable_not_delivered(self):
        # The critical property: an unverifiable send is never assumed good.
        verdict = verifier([], values={}).confirm(request_id="req-1")
        self.assertEqual(verdict.status, Verdict.UNAVAILABLE)
        self.assertFalse(verdict.ok)

    def test_nothing_to_match_on_is_unavailable(self):
        self.assertEqual(verifier([]).confirm().status, Verdict.UNAVAILABLE)

    def test_an_api_outage_is_unavailable_not_failed(self):
        # "I cannot tell" and "it did not arrive" are different answers.
        verdict = verifier([HttpTransient("connection reset")]).confirm(request_id="req-1")
        self.assertEqual(verdict.status, Verdict.UNAVAILABLE)


class TestVerdicts(unittest.TestCase):
    def test_delivery_node_ran_clean(self):
        verdict = verifier([listing(15003),
                            execution(15003, {"Webhook": None, "Deliver": None})]
                           ).confirm(request_id="req-1")
        self.assertEqual(verdict.status, Verdict.DELIVERED)
        self.assertTrue(verdict.ok)
        self.assertEqual(verdict.execution_id, "15003")

    def test_delivery_node_errored(self):
        verdict = verifier([listing(15003),
                            execution(15003, {"Deliver": "chat not found"})]
                           ).confirm(request_id="req-1")
        self.assertEqual(verdict.status, Verdict.FAILED)
        self.assertIn("chat not found", verdict.note)

    def test_workflow_ran_but_never_reached_delivery(self):
        # The 401-at-the-auth-gate shape: accepted, executed, delivered nothing.
        verdict = verifier([listing(15003),
                            execution(15003, {"Webhook": None, "Reject 401": None})]
                           ).confirm(request_id="req-1")
        self.assertEqual(verdict.status, Verdict.FAILED)
        self.assertIn("never reached", verdict.note)
        self.assertIn("Reject 401", verdict.note)

    def test_no_matching_execution(self):
        verdict = verifier([listing(15003),
                            execution(15003, {"Deliver": None}, request_id="other")]
                           ).confirm(request_id="req-1")
        self.assertEqual(verdict.status, Verdict.NOT_FOUND)

    def test_matches_on_a_needle_when_there_is_no_request_id(self):
        verdict = verifier([listing(15003),
                            execution(15003, {"Deliver": None}, request_id="anything")]
                           ).confirm(needle="lastNodeExecuted")
        self.assertEqual(verdict.status, Verdict.DELIVERED)

    def test_a_custom_delivery_node_name(self):
        checker = DeliveryVerifier(
            FakeResolver(WIRED),
            client=RecordingClient([listing(1), execution(1, {"Send Poll": None})]),
            clock=FakeClock(), delivery_node="Send Poll")
        self.assertTrue(checker.confirm(request_id="req-1").ok)


class TestWaiting(unittest.TestCase):
    """The execution record is written after the send returns."""

    def test_polls_until_the_record_appears(self):
        client = RecordingClient([
            listing(),                                              # nothing yet
            listing(15003), execution(15003, {"Deliver": None}),    # then it lands
        ])
        checker = DeliveryVerifier(FakeResolver(WIRED), client=client, clock=FakeClock())
        verdict = checker.confirm(request_id="req-1", wait_seconds=30)
        self.assertEqual(verdict.status, Verdict.DELIVERED)

    def test_gives_up_and_says_not_found(self):
        client = RecordingClient([listing() for _ in range(20)])
        checker = DeliveryVerifier(FakeResolver(WIRED), client=client, clock=FakeClock())
        verdict = checker.confirm(request_id="req-1", wait_seconds=4)
        self.assertEqual(verdict.status, Verdict.NOT_FOUND)

    def test_does_not_wait_when_told_not_to(self):
        checker = DeliveryVerifier(FakeResolver(WIRED),
                                   client=RecordingClient([listing()]), clock=FakeClock())
        checker.confirm(request_id="req-1")
        self.assertEqual(checker.clock.slept, [])


if __name__ == "__main__":
    unittest.main()
