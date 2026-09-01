"""The supervisor: noticing when the session that launched the watch is gone."""

import os
import tempfile
import time
import unittest

from helpers import *  # noqa: F401,F403
from poller.config import from_dict
from poller.engine import Engine
from poller.errors import ConfigError
from poller.model import EventReason
from poller.sinks import WHEN_FALLBACK
from poller.supervisor import ON_LOSS_IGNORE, ON_LOSS_REPORT, Supervisor

DEAD_PID = 999999


def item_reports(sink):
    """Only the reports about watched items — not watch-lifecycle events."""
    return [e for e in sink.events if e.reason not in EventReason.LIFECYCLE]


class SupervisorTests(unittest.TestCase):
    def test_no_supervisor_configured_reads_as_present(self):
        # Absent supervision must never look like *lost* supervision, or every
        # unsupervised poller would escalate on its first tick.
        sup = Supervisor({})
        self.assertFalse(sup.configured)
        self.assertTrue(sup.is_alive())
        self.assertIsNone(sup.poll())

    def test_a_live_pid_is_alive(self):
        sup = Supervisor({"pid": os.getpid()})
        self.assertTrue(sup.configured)
        self.assertTrue(sup.is_alive())

    def test_a_dead_pid_is_not(self):
        self.assertFalse(Supervisor({"pid": DEAD_PID}).is_alive())

    def test_loss_is_reported_on_the_edge_not_every_tick(self):
        sup = Supervisor({"pid": DEAD_PID})
        first = sup.poll()
        self.assertIsNotNone(first)
        self.assertIn(str(DEAD_PID), first)
        self.assertIsNone(sup.poll())
        self.assertIsNone(sup.poll())

    def test_a_fresh_heartbeat_file_counts_as_alive(self):
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            path = handle.name
        sup = Supervisor({"heartbeat_file": path, "max_age_seconds": 3600})
        self.assertTrue(sup.is_alive())

    def test_a_stale_heartbeat_file_does_not(self):
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            path = handle.name
        os.utime(path, (time.time() - 7200, time.time() - 7200))
        self.assertFalse(Supervisor({"heartbeat_file": path, "max_age_seconds": 60}).is_alive())

    def test_a_missing_heartbeat_file_is_not_alive(self):
        self.assertFalse(Supervisor({"heartbeat_file": "/nonexistent/x"}).is_alive())

    def test_an_env_reference_resolves_the_pid(self):
        from poller.envfile import EnvResolver

        sup = Supervisor({"pid": "@env:MY_PID"}, resolver=EnvResolver(None, environ={"MY_PID": "4242"}))
        self.assertEqual(sup.pid, 4242)

    def test_a_nonsense_pid_is_treated_as_unconfigured(self):
        self.assertIsNone(Supervisor({"pid": "not-a-number"}).pid)
        self.assertIsNone(Supervisor({"pid": -1}).pid)


def FallbackSink(name: str = "fallback") -> RecordingSink:
    """A recording rail that only delivers once the supervisor is gone."""
    return RecordingSink(name, when=WHEN_FALLBACK)


class FallbackRoutingTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.clock = FakeClock()

    def config(self, **overrides):
        base = {
            "name": "sup",
            "state_dir": self.dir,
            "interval_seconds": 10,
            "max_duration_hours": 0,
            "source": {"type": "http_json", "url": "https://x/y"},
            "sinks": [{"type": "stdout"}],
            "notify_on_start": False,
            "notify_on_end": False,
        }
        base.update(overrides)
        return from_dict(base)

    def engine(self, script, sinks, supervisor, **overrides):
        return Engine(self.config(**overrides), ScriptedSource(script), sinks,
                      clock=self.clock, supervisor=supervisor)

    def test_a_fallback_rail_stays_dark_while_the_supervisor_lives(self):
        primary, fallback = RecordingSink("primary"), FallbackSink()
        engine = self.engine([[], [settled("A")]], [primary, fallback],
                             Supervisor({"pid": os.getpid()}))
        engine.run(once=True)
        self.assertEqual(len(item_reports(primary)), 1)
        self.assertEqual(fallback.messages, [])

    def test_it_activates_once_the_supervisor_is_gone(self):
        primary, fallback = RecordingSink("primary"), FallbackSink()
        engine = self.engine([[], [settled("A")]], [primary, fallback],
                             Supervisor({"pid": DEAD_PID}))
        engine.run(once=True)
        self.assertEqual(len(item_reports(primary)), 1)
        self.assertEqual(len(item_reports(fallback)), 1)

    def test_the_fallback_rail_is_told_why_it_woke_up(self):
        # The handshake matters: a successor agent should learn that it exists
        # because the supervising session died, before it reads any item report.
        fallback = FallbackSink()
        engine = self.engine([[], [settled("A")]], [RecordingSink("primary"), fallback],
                             Supervisor({"pid": DEAD_PID}))
        engine.run(once=True)
        self.assertEqual(fallback.events[0].reason, EventReason.SUPERVISOR_LOST)

    def test_the_loss_itself_is_reported_once(self):
        primary = RecordingSink("primary")
        engine = self.engine([[], [], []], [primary], Supervisor({"pid": DEAD_PID}))
        engine.run(once=True)
        engine.tick()
        engine.tick()
        lost = [e for e in primary.events if e.reason == EventReason.SUPERVISOR_LOST]
        self.assertEqual(len(lost), 1)
        self.assertIn(str(DEAD_PID), lost[0].body)

    def test_on_loss_report_notifies_without_activating_fallback_rails(self):
        primary, fallback = RecordingSink("primary"), FallbackSink()
        engine = self.engine([[], [settled("A")]], [primary, fallback],
                             Supervisor({"pid": DEAD_PID, "on_loss": ON_LOSS_REPORT}))
        engine.run(once=True)
        self.assertFalse(engine.fallback_active)
        self.assertEqual(fallback.messages, [])
        self.assertTrue([e for e in primary.events if e.reason == EventReason.SUPERVISOR_LOST])

    def test_on_loss_ignore_stays_quiet(self):
        primary = RecordingSink("primary")
        engine = self.engine([[], []], [primary],
                             Supervisor({"pid": DEAD_PID, "on_loss": ON_LOSS_IGNORE}))
        engine.run(once=True)
        self.assertFalse(engine.fallback_active)

    def test_an_unsupervised_poller_never_activates_fallback_rails(self):
        primary, fallback = RecordingSink("primary"), FallbackSink()
        engine = self.engine([[], [settled("A")]], [primary, fallback], Supervisor({}))
        engine.run(once=True)
        self.assertFalse(engine.fallback_active)
        self.assertEqual(fallback.messages, [])

    def test_past_reports_are_not_replayed_when_the_supervisor_later_dies(self):
        # The fallback exists to escalate *future* events, not to re-deliver the
        # backlog the primary rails already handled.
        primary, fallback = RecordingSink("primary"), FallbackSink()
        sup = Supervisor({"pid": os.getpid()})
        engine = self.engine([[], [settled("A")], [settled("A")]], [primary, fallback], sup)
        engine.run(once=True)
        sup.pid = DEAD_PID          # the session goes away
        sup.cmdline = None
        engine.tick()
        self.assertEqual(item_reports(fallback), [])   # no replay of A
        self.assertEqual([e.reason for e in fallback.events], [EventReason.SUPERVISOR_LOST])

    def test_an_invalid_on_loss_is_rejected_at_config_time(self):
        with self.assertRaises(ConfigError):
            self.config(supervisor={"pid": 1, "on_loss": "panic"})


if __name__ == "__main__":
    unittest.main()
