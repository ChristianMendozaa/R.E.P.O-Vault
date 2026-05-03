import unittest

from repo_vault.inventory_logic import (
    add_item,
    apply_have_everything,
    build_type_id_map,
    calculate_item_totals,
    remove_item,
)
from repo_vault.items import STATIC_ITEM_IDS

from tests.helpers import load_test_save


class InventoryLogicTests(unittest.TestCase):
    def setUp(self):
        self.data = load_test_save()
        self.root_data = self.data["dictionaryOfDictionaries"]["value"]
        self.type_id_map = build_type_id_map(self.root_data, STATIC_ITEM_IDS)

    def test_build_type_id_map_contains_static_and_dynamic_ids(self):
        self.assertIn("Item Power Crystal", self.type_id_map)
        self.assertEqual(self.type_id_map["Item Power Crystal"], STATIC_ITEM_IDS["Item Power Crystal"])

    def test_add_item_increments_quantity_and_forces_shop_state(self):
        item_name = "Item Power Crystal"
        before = int(self.root_data.get("itemsPurchased", {}).get(item_name, 0))

        new_qty, new_key = add_item(self.root_data, self.type_id_map, item_name)

        self.assertEqual(new_qty, before + 1)
        self.assertIn(new_key, self.root_data["itemStatBattery"])
        self.assertEqual(self.root_data["runStats"]["save level"], 1)

    def test_remove_item_decrements_quantity_and_removes_last_instance(self):
        item_name = "Item Power Crystal"
        add_item(self.root_data, self.type_id_map, item_name)
        before = int(self.root_data["itemsPurchased"][item_name])

        new_qty, removed_key = remove_item(self.root_data, item_name)

        self.assertEqual(new_qty, before - 1)
        if removed_key is not None:
            self.assertNotIn(removed_key, self.root_data["itemStatBattery"])
        self.assertEqual(self.root_data["runStats"]["save level"], 1)

    def test_have_everything_populates_missing_items(self):
        self.root_data["itemsPurchased"] = {}
        self.root_data["itemStatBattery"] = {}
        self.root_data["item"] = {}

        added_count = apply_have_everything(self.root_data, self.type_id_map)
        total_qty, unique_qty = calculate_item_totals(self.root_data)

        self.assertEqual(added_count, len(self.type_id_map))
        self.assertEqual(total_qty, len(self.type_id_map))
        self.assertEqual(unique_qty, len(self.type_id_map))
        self.assertEqual(self.root_data["runStats"]["save level"], 1)
