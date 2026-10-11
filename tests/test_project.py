import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from main import validate  # noqa: E402


class ProjectConfigTests(unittest.TestCase):
    def test_project_configuration_is_valid(self):
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
