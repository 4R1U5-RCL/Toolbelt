"""The verdict rules — including the one this package exists to encode."""

import unittest

from sentinel import classify


class TestAideExitCodes(unittest.TestCase):
    def test_zero_is_clean(self):
        result = classify.classify_aide("h", 0, "AIDE found NO differences")
        self.assertEqual(result.verdict, classify.CLEAN)

    def test_non_zero_is_a_finding_not_a_crash(self):
        """The recorded failure: aide exits non-zero when it SUCCEEDS at detecting.

        Reproduces the negative control run on a production host, 2026-09-01 —
        one watched file appended to, re-checked, exit=4, one changed entry.
        """
        stdout = ("Summary:\n  Changed entries: 1\n"
                  "File: /srv/tree/config.conf\n"
                  "  Size    : 17        | 26\n")
        result = classify.classify_aide("h", 4, stdout)
        self.assertEqual(result.verdict, classify.FINDING)
        self.assertIn("changed files", result.headline)
        self.assertTrue(result.evidence)

    def test_bitmask_decomposes(self):
        self.assertEqual(classify.describe_aide_bits(1), "new files")
        self.assertEqual(classify.describe_aide_bits(2), "removed files")
        self.assertEqual(classify.describe_aide_bits(4), "changed files")
        self.assertEqual(classify.describe_aide_bits(7),
                         "new files, removed files, changed files")

    def test_all_difference_codes_are_findings(self):
        for code in range(1, 8):
            with self.subTest(code=code):
                self.assertEqual(classify.classify_aide("h", code, "").verdict,
                                 classify.FINDING)

    def test_aide_error_codes_are_errors_not_findings(self):
        """18 is AIDE's IO error. It says nothing about the host and must not
        be reported as if the host changed."""
        result = classify.classify_aide("h", 18, "", "IO error")
        self.assertEqual(result.verdict, classify.ERROR)

    def test_unmapped_code_is_an_error_never_clean(self):
        for code in (8, 13, 99, -1):
            with self.subTest(code=code):
                self.assertEqual(classify.classify_aide("h", code, "").verdict,
                                 classify.ERROR)


class TestFingerprint(unittest.TestCase):
    HASH = "d6aa449cd0b55f8763c2db5644125761ef3d8616a35746ef1af5112f82443d45"

    def test_match_is_clean(self):
        observed = f"{self.HASH}  /var/lib/aide/aide.db"
        result = classify.classify_fingerprint("h", observed, self.HASH)
        self.assertEqual(result.verdict, classify.CLEAN)

    def test_mismatch_is_a_finding_and_says_it_is_not_a_verdict(self):
        result = classify.classify_fingerprint("h", "0" * 64, self.HASH)
        self.assertEqual(result.verdict, classify.FINDING)
        self.assertIn("a verdict on its own", result.detail)

    def test_no_record_is_unbaselined_not_clean(self):
        result = classify.classify_fingerprint("h", self.HASH, None)
        self.assertEqual(result.verdict, classify.UNBASELINED)

    def test_unreadable_db_is_an_error(self):
        result = classify.classify_fingerprint("h", None, self.HASH)
        self.assertEqual(result.verdict, classify.ERROR)


class TestDebsums(unittest.TestCase):
    def test_clean(self):
        result = classify.classify_debsums("h", 0, "")
        self.assertEqual(result.verdict, classify.CLEAN)

    def test_changed_files_are_findings(self):
        stdout = "/usr/bin/ls\n/etc/ssh/sshd_config\n"
        result = classify.classify_debsums("h", 2, stdout)
        self.assertEqual(result.verdict, classify.FINDING)
        self.assertEqual(len(result.evidence), 2)

    def test_absent_tool_is_skipped(self):
        result = classify.classify_debsums("h", 127, "", "sh: 1: debsums: not found")
        self.assertEqual(result.verdict, classify.SKIPPED)

    def test_missing_file_output_is_not_mistaken_for_an_absent_tool(self):
        """'not found' in the FINDINGS must not read as 'tool not installed'."""
        stdout = "debsums: missing file /usr/bin/foo (from bar package): not found\n"
        result = classify.classify_debsums("h", 2, stdout, "")
        self.assertEqual(result.verdict, classify.FINDING)


class TestRootkitScanners(unittest.TestCase):
    def test_clean(self):
        result = classify.classify_rootkit("h", "rkhunter", 0, "")
        self.assertEqual(result.verdict, classify.CLEAN)

    def test_warning_is_a_finding(self):
        result = classify.classify_rootkit("h", "rkhunter", 1,
                                           "Warning: /usr/bin/x replaced\n")
        self.assertEqual(result.verdict, classify.FINDING)

    def test_infected_is_a_finding(self):
        result = classify.classify_rootkit("h", "chkrootkit", 0, "Checking x... INFECTED\n")
        self.assertEqual(result.verdict, classify.FINDING)

    def test_absent_tool_is_skipped(self):
        result = classify.classify_rootkit("h", "chkrootkit", 127, "",
                                           "sh: 1: chkrootkit: not found")
        self.assertEqual(result.verdict, classify.SKIPPED)


class TestWorst(unittest.TestCase):
    def make(self, verdict):
        return classify.CheckResult("h", "c", verdict, "")

    def test_finding_outranks_everything(self):
        results = [self.make(classify.CLEAN), self.make(classify.ERROR),
                   self.make(classify.FINDING)]
        self.assertEqual(classify.worst(results), classify.FINDING)

    def test_error_outranks_unbaselined_and_clean(self):
        results = [self.make(classify.CLEAN), self.make(classify.UNBASELINED),
                   self.make(classify.ERROR)]
        self.assertEqual(classify.worst(results), classify.ERROR)

    def test_empty_sweep_is_not_clean(self):
        self.assertNotEqual(classify.worst([]), classify.CLEAN)


if __name__ == "__main__":
    unittest.main()
