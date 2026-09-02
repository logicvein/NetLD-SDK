import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_cmd_and_export_log import ExampleError, build_job, safe_filename  # noqa: E402


class AdvancedCommandExampleTests(unittest.TestCase):
    def test_build_job_uses_current_job_shape(self):
        job = build_job("Lab", "192.0.2.10", ["show version", "show clock"])
        self.assertEqual(job["managedNetworks"], ["Lab"])
        self.assertEqual(job["jobType"], "Script Tool Job")
        self.assertEqual(job["jobParameters"]["ipResolutionScheme"], "ipCsv")
        self.assertEqual(job["jobParameters"]["ipResolutionData"], '"192.0.2.10@Lab"')
        self.assertEqual(job["jobParameters"]["input.commandList"], "show version\nshow clock")
        self.assertEqual(job["jobParameters"]["backupOnCompletion"], "false")

    def test_empty_command_list_is_rejected(self):
        with self.assertRaises(ExampleError):
            build_job("Lab", "192.0.2.10", [])

    def test_filename_is_sanitized(self):
        self.assertEqual(safe_filename("Lab / 192.0.2.10"), "Lab_192.0.2.10")


if __name__ == "__main__":
    unittest.main()

