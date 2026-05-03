import json

from .constants import SAVE_PASSWORD
from .oxide_cipher import unwrap_payload, wrap_payload


def load_save_data(file_path):
    decrypted_data = unwrap_payload(file_path, SAVE_PASSWORD)
    return json.loads(decrypted_data)


def save_save_data(file_path, json_data):
    encrypted_data = wrap_payload(
        json.dumps(json_data, indent=4).encode("utf-8"),
        SAVE_PASSWORD,
    )
    with open(file_path, "wb") as file_handle:
        file_handle.write(encrypted_data)
