import unittest

from repo_vault.app import EditorApp
from repo_vault.constants import STATE_OPTIONS
from repo_vault.theme import COLORS

from tests.helpers import FakeEntry, FakeLabel, load_test_save


class EditorAppLogicTests(unittest.TestCase):
    def make_app(self):
        app = EditorApp.__new__(EditorApp)
        app.json_data = load_test_save()
        app.current_file_path = "dummy.es3"
        app.savefilename = "dummy.es3"
        app.has_unsaved_changes = False
        app.header_file_label = FakeLabel()
        app.status_badge = FakeLabel()
        app.players = []
        app.player_entries = {}
        app.player_images = []
        app.nav_buttons = {}
        app.field_entries = {}
        app.entry_game_state = None
        return app

    def test_get_item_totals_matches_save_data(self):
        app = self.make_app()
        total, unique = app.get_item_totals()
        self.assertGreaterEqual(total, unique)
        self.assertGreaterEqual(unique, 0)

    def test_get_save_state_label_maps_valid_values(self):
        app = self.make_app()
        app.json_data["dictionaryOfDictionaries"]["value"]["runStats"]["save level"] = 1
        self.assertEqual(app.get_save_state_label(), STATE_OPTIONS[1])

    def test_set_numeric_value_updates_target_and_marks_dirty(self):
        app = self.make_app()
        entry = FakeEntry("123")
        target = {}

        app.set_numeric_value(entry, target, "currency", "Currency changed")

        self.assertEqual(target["currency"], 123)
        self.assertTrue(app.has_unsaved_changes)
        self.assertEqual(app.header_file_label.text, "dummy.es3 *")
        self.assertEqual(app.status_badge.text, "Currency changed")
        self.assertEqual(entry.border_color, COLORS["border"])

    def test_set_numeric_value_rejects_invalid_input(self):
        app = self.make_app()
        entry = FakeEntry("abc")
        target = {"currency": 77}

        app.set_numeric_value(entry, target, "currency", "Currency changed")

        self.assertEqual(target["currency"], 77)
        self.assertFalse(app.has_unsaved_changes)
        self.assertEqual(app.status_badge.text, "Only whole numbers are allowed here")
        self.assertEqual(entry.border_color, COLORS["danger"])

    def test_set_text_value_updates_target(self):
        app = self.make_app()
        entry = FakeEntry("Vault Team")
        target = {"value": "Old Team"}

        app.set_text_value(entry, target, "value", "Team changed")

        self.assertEqual(target["value"], "Vault Team")
        self.assertTrue(app.has_unsaved_changes)
        self.assertEqual(app.status_badge.text, "Team changed")

    def test_mark_saved_clears_unsaved_indicator(self):
        app = self.make_app()
        app.has_unsaved_changes = True

        app.mark_saved("Save stored")

        self.assertFalse(app.has_unsaved_changes)
        self.assertEqual(app.header_file_label.text, "dummy.es3")
        self.assertEqual(app.status_badge.text, "Save stored")
