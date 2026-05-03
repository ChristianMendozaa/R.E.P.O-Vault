import tempfile
import unittest
from pathlib import Path

from repo_vault.save_service import load_save_data, save_save_data

from tests.helpers import TEST_SAVE_PATH, load_test_save


class SaveServiceTests(unittest.TestCase):
    def test_load_test_save_returns_expected_shape(self):
        data = load_save_data(TEST_SAVE_PATH)
        self.assertIn("teamName", data)
        self.assertIn("playerNames", data)
        self.assertIn("dictionaryOfDictionaries", data)
        self.assertIn("runStats", data["dictionaryOfDictionaries"]["value"])

    def test_roundtrip_preserves_core_data(self):
        data = load_test_save()
        data["teamName"]["value"] = "Regression Squad"
        data["dictionaryOfDictionaries"]["value"]["runStats"]["currency"] = 987

        with tempfile.TemporaryDirectory(dir="C:\\tmp") as temp_dir:
            output_path = Path(temp_dir) / "roundtrip.es3"
            save_save_data(output_path, data)
            reloaded = load_save_data(output_path)

        self.assertEqual(reloaded["teamName"]["value"], "Regression Squad")
        self.assertEqual(reloaded["dictionaryOfDictionaries"]["value"]["runStats"]["currency"], 987)
        self.assertEqual(reloaded["playerNames"]["value"], data["playerNames"]["value"])
