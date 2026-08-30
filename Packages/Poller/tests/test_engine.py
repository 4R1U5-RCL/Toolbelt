"""Engine behaviour — including a regression test for the incident that caused
this package to exist: a watch pinned to one submission missed the settle of a
different one."""

import json
import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403
from poller.config import from_dict
from poller.engine import EXIT_FATAL, EXIT_LOCKED, EXIT_OK, Engine
from poller.errors import FatalSourceError, TransientSourceError
from poller.lock import InstanceLock
from poller.model import EventReason
from poller.state import Store


def reasons_of(sink):
    return [event.reason for event in sink.events]


def item_reports(sink):
    return [e for e in sink.events if e.reason not in EventReason.LIFECYCLE]


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.clock = FakeClock()

    def config(self, **overrides):
        base = {
            "name": "test",
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

    def engine(self, script, sinks=None, config=None, **overrides):
        sinks = sinks if sinks is not None else [RecordingSink("main")]
        return Engine(config or self.config(**overrides), ScriptedSource(script), sinks,
                      clock=self.clock)


class ReportingTests(EngineTestCase):
    def test_a_new_settle_is_reported_once_and_only_once(self):
        sink = RecordingSink("main")
        engine = self.engine([[], [settled("A")], [settled("A")]], [sink])
        engine.run(once=True)      # seed on an empty board, then tick -> A settles
        engine.tick()              # A is still there; it must not be reported again
        self.assertEqual(len(item_reports(sink)), 1)
        self.assertEqual(item_reports(sink)[0].item.key, "A")

    def test_a_different_item_settling_is_also_reported(self):
        # THE regression test. The old poller watched one hard-coded notebook
        # slug; when a different submission settled, nothing fired. Identity is
        # per item, and the watch covers the whole collection.
        sink = RecordingSink("main")
        engine = self.engine([[settled("A")], [settled("A"), settled("B")]], [sink])
        engine.run(once=True)
        keys = [e.item.key for e in item_reports(sink)]
        self.assertEqual(keys, ["B"])

    def test_seeding_suppresses_history_and_records_the_count(self):
        sink = RecordingSink("main")
        engine = self.engine([[settled("A"), settled("B"), pending("C")]], [sink])
        engine.run(once=True)
        self.assertEqual(item_reports(sink), [])
        store = Store(engine.config.state_file)
        self.assertIsNotNone(store.seeded_at)
        self.assertEqual(store.stats()["seeded"], 2)

    def test_no_seed_reports_everything_already_terminal(self):
        sink = RecordingSink("main")
        engine = self.engine([[settled("A"), settled("B")]], [sink])
        engine.run(once=True, seed=False)
        self.assertEqual(sorted(e.item.key for e in item_reports(sink)), ["A", "B"])

    def test_pending_then_settled_produces_exactly_one_report(self):
        sink = RecordingSink("main")
        engine = self.engine([[], [pending("A")], [pending("A")], [settled("A", "51.210")]], [sink])
        engine.run(once=True)
        engine.tick()
        engine.tick()
        reports = item_reports(sink)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].reason, EventReason.SETTLED)
        self.assertIn("51.210", reports[0].item.fields["score"])

    def test_failed_items_are_reported_distinctly_from_settled_ones(self):
        sink = RecordingSink("main")
        engine = self.engine([[], [failed("A", "kernel timeout")]], [sink])
        engine.run(once=True)
        report = item_reports(sink)[0]
        self.assertEqual(report.reason, EventReason.FAILED)
        self.assertEqual(report.severity, "error")
        self.assertIn("kernel timeout", report.body)

    def test_a_pending_item_past_its_sla_is_reported_once(self):
        sink = RecordingSink("main")
        engine = self.engine([[], [pending("A")]], [sink], stale_after_seconds=3600)
        engine.run(once=True)
        self.assertEqual(item_reports(sink), [])   # not stale yet
        self.clock.advance(7200)
        engine.tick()
        engine.tick()
        stale = [e for e in item_reports(sink) if e.reason == EventReason.STALE]
        self.assertEqual(len(stale), 1)


class DeliveryTests(EngineTestCase):
    def test_a_failed_rail_is_retried_and_a_delivered_one_is_not(self):
        good = RecordingSink("good")
        flaky = FlakySink("flaky", fail_times=1)
        engine = self.engine([[], [settled("A")], [settled("A")]], [good, flaky])
        engine.run(once=True)
        self.assertEqual(len(item_reports(good)), 1)
        self.assertEqual(flaky.messages, [])
        engine.tick()                      # the ledger retries only the flaky rail
        self.assertEqual(len(item_reports(good)), 1)
        self.assertEqual(len(flaky.messages), 1)

    def test_a_fatally_broken_rail_is_not_retried_forever(self):
        dead = DeadSink("dead")
        engine = self.engine([[], [settled("A")], [settled("A")], [settled("A")]], [dead])
        engine.run(once=True)
        engine.tick()
        engine.tick()
        self.assertEqual(dead.attempts, 1)

    def test_delivery_is_abandoned_after_the_attempt_budget(self):
        flaky = FlakySink("flaky", fail_times=99)
        engine = self.engine([[], [settled("A")]] + [[settled("A")]] * 6, [flaky],
                             max_delivery_attempts=3)
        engine.run(once=True)
        for _ in range(5):
            engine.tick()
        self.assertEqual(flaky.attempts, 3)
        store = Store(engine.config.state_file)
        self.assertEqual([r.dedup_key for r in store.records.values() if r.abandoned], ["A:settled"])

    def test_an_undelivered_report_survives_a_restart(self):
        config = self.config()
        first = Engine(config, ScriptedSource([[], [settled("A")]]),
                       [FlakySink("rail", fail_times=99)], clock=self.clock)
        first.run(once=True)

        recovered = RecordingSink("rail")   # same name = same ledger slot
        second = Engine(config, ScriptedSource([[]]), [recovered], clock=self.clock)
        second.run(once=True)
        self.assertEqual([e.item.key for e in item_reports(recovered)], ["A"])

    def test_a_sink_raising_an_unexpected_error_does_not_kill_the_watch(self):
        class Exploding(RecordingSink):
            def send(self, message, event):
                raise RuntimeError("bug in a sink")

        engine = self.engine([[], [settled("A")]], [Exploding("boom")])
        self.assertEqual(engine.run(once=True), EXIT_OK)

    def test_a_sink_filtered_event_completes_instead_of_retrying_forever(self):
        filtered = RecordingSink("filtered", reasons=[EventReason.FAILED])
        engine = self.engine([[], [settled("A")]], [filtered])
        engine.run(once=True)
        store = Store(engine.config.state_file)
        record = store.get("A:settled")
        self.assertEqual(record.outstanding(["filtered"]), [])
        self.assertEqual(filtered.messages, [])


class SurvivabilityTests(EngineTestCase):
    def test_a_transient_fetch_failure_does_not_stop_the_watch(self):
        sink = RecordingSink("main")
        engine = self.engine([[], TransientSourceError("timeout"), [settled("A")]], [sink])
        engine.run(once=True)          # seed, then a tick that fails
        self.assertEqual(item_reports(sink), [])
        engine.tick()                  # recovers and reports
        self.assertEqual(len(item_reports(sink)), 1)

    def test_repeated_failures_raise_a_degraded_alarm_once(self):
        sink = RecordingSink("main")
        engine = self.engine([[], TransientSourceError("timeout")], [sink],
                             degraded_after_failures=2)
        engine.run(once=True)
        engine.tick()
        engine.tick()
        degraded = [r for r in reasons_of(sink) if r == EventReason.DEGRADED]
        self.assertEqual(len(degraded), 1)

    def test_a_fatal_source_error_is_announced_and_exits_nonzero(self):
        sink = RecordingSink("main")
        source = ScriptedSource([FatalSourceError("HTTP 401: bad token")], preflight_ok=False)
        engine = Engine(self.config(notify_on_end=True), source, [sink], clock=self.clock)
        self.assertEqual(engine.run(once=True), EXIT_FATAL)
        failures = [e for e in sink.events if e.reason == EventReason.WATCH_FAILED]
        self.assertEqual(len(failures), 1)
        self.assertIn("401", failures[0].body)

    def test_the_end_of_a_watch_is_always_announced(self):
        # The failure that started all this: a poller self-exited on its own
        # sentinel and nothing told anyone the watch was over.
        sink = RecordingSink("main")
        engine = self.engine([[]], [sink], notify_on_end=True,
                             max_duration_hours=20.0 / 3600.0)
        self.assertEqual(engine.run(), EXIT_OK)
        ended = [e for e in sink.events if e.reason == EventReason.WATCH_ENDED]
        self.assertEqual(len(ended), 1)
        self.assertIn("max duration", ended[0].body)

    def test_a_stop_signal_ends_the_watch_with_a_report(self):
        sink = RecordingSink("main")
        engine = self.engine([[]], [sink], notify_on_end=True)
        engine.stop_event.set()
        engine.run()
        ended = [e for e in sink.events if e.reason == EventReason.WATCH_ENDED]
        self.assertEqual(len(ended), 1)
        self.assertIn("stop signal", ended[0].body)

    def test_an_unexpected_crash_is_still_reported(self):
        class Exploding(ScriptedSource):
            def fetch(self):
                raise RuntimeError("something nobody predicted")

        sink = RecordingSink("main")
        engine = Engine(self.config(), Exploding([]), [sink], clock=self.clock)
        self.assertEqual(engine.run(once=True), EXIT_FATAL)
        self.assertEqual([e.reason for e in sink.events], [EventReason.WATCH_FAILED])

    def test_a_second_instance_refuses_to_start(self):
        config = self.config()
        holder = InstanceLock(config.lock_file, config.name)
        holder.acquire()
        engine = self.engine([[]], config=config)
        self.assertEqual(engine.run(once=True), EXIT_LOCKED)
        holder.release()

    def test_the_heartbeat_file_makes_liveness_observable_from_outside(self):
        engine = self.engine([[], [pending("A")]])
        engine.run(once=True)
        with open(engine.config.heartbeat_file, encoding="utf-8") as handle:
            beat = json.load(handle)
        self.assertEqual(beat["name"], "test")
        self.assertEqual(beat["status"], "ended")
        self.assertEqual(beat["ticks"], 1)
        self.assertIn("main", beat["sinks"])

    def test_a_periodic_alive_ping_can_be_enabled(self):
        sink = RecordingSink("main")
        engine = self.engine([[]], [sink], heartbeat_every_ticks=2)
        engine.run(once=True)
        self.assertEqual([r for r in reasons_of(sink) if r == EventReason.HEARTBEAT], [])
        engine.tick()
        self.assertEqual([r for r in reasons_of(sink) if r == EventReason.HEARTBEAT],
                         [EventReason.HEARTBEAT])

    def test_jitter_spreads_the_polling_interval(self):
        import random

        engine = self.engine([[]], jitter_seconds=5, max_duration_hours=25.0 / 3600.0)
        engine.rand = random.Random(1)
        engine.run()
        self.assertTrue(all(10 <= delay <= 15 for delay in self.clock.slept), self.clock.slept)


if __name__ == "__main__":
    unittest.main()


class StartupTests(EngineTestCase):
    def test_a_long_watch_preflights_before_committing_to_it(self):
        class Counting(ScriptedSource):
            preflights = 0

            def preflight(self):
                Counting.preflights += 1

        source = Counting([[]])
        config = self.config(max_duration_hours=1.0 / 3600.0, seed_on_first_run=False)
        Engine(config, source, [RecordingSink("main")], clock=self.clock).run()
        self.assertEqual(Counting.preflights, 1)

    def test_seeding_is_itself_the_preflight(self):
        # A fresh store seeds, and the seed fetch already proves the credentials —
        # so it must not also pay for a separate probe.
        class Counting(ScriptedSource):
            preflights = 0

            def preflight(self):
                Counting.preflights += 1

        source = Counting([[]])
        Engine(self.config(), source, [RecordingSink("main")], clock=self.clock).run(once=True)
        self.assertEqual(Counting.preflights, 0)
        self.assertEqual(source.calls, 2)   # the seed fetch, then one tick

    def test_a_single_tick_run_does_not_pay_for_a_separate_preflight(self):
        class Counting(ScriptedSource):
            preflights = 0

            def preflight(self):
                Counting.preflights += 1

        source = Counting([[]])
        store_path = self.config().state_file
        Engine(self.config(), ScriptedSource([[]]), [RecordingSink("x")], clock=self.clock).run(once=True)
        self.assertTrue(os.path.exists(store_path))   # state now exists: not a fresh run
        engine = Engine(self.config(), source, [RecordingSink("main")], clock=self.clock)
        engine.run(once=True)
        self.assertEqual(Counting.preflights, 0)
        self.assertEqual(source.calls, 1)             # exactly one API call for one tick
