import json
import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403
from poller.model import Event, EventReason
from poller.state import Store


def _event(key="K1", reason=EventReason.SETTLED):
    return Event(reason=reason, dedup_key="{0}:settled".format(key), title="t", body="b",
                 severity="info", item=settled(key))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "s.json")
        self.clock = FakeClock()

    def store(self, **kwargs):
        return Store(self.path, clock=self.clock, **kwargs)

    def test_fresh_store_reports_itself_as_fresh(self):
        self.assertTrue(self.store().was_fresh)

    def test_records_survive_a_reload(self):
        store = self.store()
        store.enroll(_event())
        store.save()
        reloaded = self.store()
        self.assertFalse(reloaded.was_fresh)
        self.assertTrue(reloaded.knows("K1:settled"))

    def test_enroll_is_idempotent(self):
        store = self.store()
        first = store.enroll(_event())
        second = store.enroll(_event())
        self.assertIs(first, second)
        self.assertEqual(len(store.records), 1)

    def test_delivery_is_tracked_per_sink(self):
        store = self.store()
        record = store.enroll(_event())
        store.mark_delivered(record, "slack")
        self.assertEqual(record.outstanding(["slack", "telegram"]), ["telegram"])
        self.assertFalse(record.is_complete(["slack", "telegram"]))
        store.mark_delivered(record, "telegram")
        self.assertTrue(record.is_complete(["slack", "telegram"]))

    def test_a_fatally_failed_sink_is_not_retried(self):
        store = self.store()
        record = store.enroll(_event())
        store.mark_failed(record, "slack", "token revoked", fatal=True)
        self.assertEqual(record.outstanding(["slack", "telegram"]), ["telegram"])

    def test_undelivered_respects_the_attempt_budget(self):
        store = self.store()
        record = store.enroll(_event())
        store.mark_failed(record, "slack", "boom")
        for _ in range(3):
            store.note_attempt(record, max_attempts=3)
        self.assertTrue(record.abandoned)
        self.assertEqual(store.undelivered(["slack"], max_attempts=3), [])

    def test_seeded_records_are_never_delivered(self):
        store = self.store()
        record = store.enroll(_event(), seeded=True)
        self.assertEqual(record.outstanding(["slack"]), [])
        self.assertEqual(store.undelivered(["slack"], 5), [])

    def test_observe_stamps_first_sight_once(self):
        store = self.store()
        first = store.observe("K1")
        self.clock.advance(600)
        self.assertEqual(store.observe("K1"), first)

    def test_round_trips_an_event_for_delivery_after_a_restart(self):
        store = self.store()
        store.enroll(_event())
        store.save()
        record = self.store().get("K1:settled")
        event = record.to_event()
        self.assertEqual(event.dedup_key, "K1:settled")
        self.assertEqual(event.item.key, "K1")
        self.assertEqual(event.context()["score"], "1.000")

    def test_corrupt_state_is_preserved_and_the_store_starts_clean(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{ truncated")
        store = self.store()
        self.assertTrue(store.was_fresh)
        self.assertEqual(store.records, {})
        backups = [n for n in os.listdir(self.dir) if ".corrupt-" in n]
        self.assertEqual(len(backups), 1)

    def test_a_future_schema_is_not_silently_misread(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump({"schema": 99, "records": {"x": {}}}, handle)
        store = self.store()
        self.assertTrue(store.was_fresh)
        self.assertEqual(store.records, {})

    def test_pruning_bounds_the_file(self):
        store = self.store(max_records=5)
        for index in range(12):
            self.clock.advance(1)
            store.enroll(_event("K{0}".format(index)))
        self.assertLessEqual(len(store.records), 5)
        # Newest survive; the oldest are the ones dropped.
        self.assertTrue(store.knows("K11:settled"))

    def test_writes_are_atomic_and_leave_no_temp_files(self):
        store = self.store()
        store.enroll(_event())
        store.save()
        self.assertEqual([n for n in os.listdir(self.dir) if ".tmp." in n], [])
        with open(self.path, "r", encoding="utf-8") as handle:
            json.load(handle)  # a complete, parseable document


if __name__ == "__main__":
    unittest.main()


class DirtyTrackingTests(unittest.TestCase):
    """An idle tick must not cost an fsync — observed as multi-second ticks on a
    slow overlay filesystem during the live smoke test."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "s.json")

    def test_a_store_with_no_changes_does_not_rewrite_the_file(self):
        store = Store(self.path, clock=FakeClock())
        store.enroll(_event())
        store.save()
        before = os.stat(self.path).st_mtime_ns
        store.save()
        store.save()
        self.assertEqual(os.stat(self.path).st_mtime_ns, before)

    def test_a_change_makes_the_next_save_write(self):
        store = Store(self.path, clock=FakeClock())
        store.save(force=True)
        first = os.path.getsize(self.path)
        store.enroll(_event())
        store.save()
        self.assertGreater(os.path.getsize(self.path), first)

    def test_observing_a_new_item_marks_the_store_dirty(self):
        store = Store(self.path, clock=FakeClock())
        store.observe("A")
        store.save()
        self.assertTrue(os.path.exists(self.path))
