from copy import deepcopy
from pathlib import Path

from repo_vault.save_service import load_save_data


TEST_SAVE_PATH = Path(__file__).resolve().parent.parent / "test.es3"


def load_test_save():
    return deepcopy(load_save_data(TEST_SAVE_PATH))


class FakeEntry:
    def __init__(self, value=""):
        self.value = str(value)
        self.border_color = None

    def get(self):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, _index, value):
        self.value = str(value)

    def configure(self, **kwargs):
        if "border_color" in kwargs:
            self.border_color = kwargs["border_color"]


class FakeLabel:
    def __init__(self, text=""):
        self.text = text

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
