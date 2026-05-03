import importlib
import unittest


class SmokeTests(unittest.TestCase):
    def test_main_module_imports(self):
        module = importlib.import_module("main")
        self.assertTrue(hasattr(module, "launch"))

    def test_repo_modules_import(self):
        for module_name in [
            "repo_vault.app",
            "repo_vault.constants",
            "repo_vault.hovercard",
            "repo_vault.inventory_logic",
            "repo_vault.items",
            "repo_vault.oxide_cipher",
            "repo_vault.players",
            "repo_vault.resources",
            "repo_vault.save_service",
            "repo_vault.theme",
            "repo_vault.widgets",
        ]:
            with self.subTest(module=module_name):
                importlib.import_module(module_name)
