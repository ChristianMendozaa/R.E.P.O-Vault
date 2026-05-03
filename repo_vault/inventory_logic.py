def build_type_id_map(root_data, static_item_ids):
    type_id_map = dict(static_item_ids)
    for key, value in root_data.get("item", {}).items():
        if "/" not in key:
            continue
        base_name = key.rsplit("/", 1)[0]
        if base_name not in type_id_map:
            type_id_map[base_name] = value
    return type_id_map


def ensure_item_containers(root_data):
    purch_dict = root_data.setdefault("itemsPurchased", {})
    sb_dict = root_data.setdefault("itemStatBattery", {})
    imap_dict = root_data.setdefault("item", {})
    return purch_dict, sb_dict, imap_dict


def next_item_index(sb_dict, base_name):
    existing = [
        int(key.rsplit("/", 1)[1])
        for key in sb_dict
        if key.startswith(base_name + "/") and key.rsplit("/", 1)[1].isdigit()
    ]
    return (max(existing) + 1) if existing else 1


def force_shop_state(run_stats):
    run_stats["save level"] = 1


def add_item(root_data, type_id_map, item_name, battery_value=100):
    purch_dict, sb_dict, imap_dict = ensure_item_containers(root_data)
    type_id = type_id_map.get(item_name, 0)
    new_key = f"{item_name}/{next_item_index(sb_dict, item_name)}"
    sb_dict[new_key] = battery_value
    imap_dict[new_key] = type_id
    imap_dict.setdefault(item_name, 0)
    purch_dict[item_name] = int(purch_dict.get(item_name, 0)) + 1
    force_shop_state(root_data["runStats"])
    return purch_dict[item_name], new_key


def remove_item(root_data, item_name):
    purch_dict, sb_dict, imap_dict = ensure_item_containers(root_data)
    current_qty = int(purch_dict.get(item_name, 0))
    if current_qty <= 0:
        return 0, None

    existing = sorted(
        [
            int(key.rsplit("/", 1)[1])
            for key in sb_dict
            if key.startswith(item_name + "/") and key.rsplit("/", 1)[1].isdigit()
        ]
    )
    removed_key = None
    if existing:
        removed_key = f"{item_name}/{existing[-1]}"
        sb_dict.pop(removed_key, None)
        imap_dict.pop(removed_key, None)

    purch_dict[item_name] = max(0, current_qty - 1)
    if purch_dict[item_name] == 0:
        del purch_dict[item_name]

    force_shop_state(root_data["runStats"])
    return purch_dict.get(item_name, 0), removed_key


def apply_have_everything(root_data, type_id_map, battery_value=100):
    purch_dict, sb_dict, imap_dict = ensure_item_containers(root_data)
    added_count = 0
    for item_name in sorted(type_id_map.keys()):
        if int(purch_dict.get(item_name, 0)) != 0:
            continue
        type_id = type_id_map.get(item_name, 0)
        new_key = f"{item_name}/{next_item_index(sb_dict, item_name)}"
        sb_dict[new_key] = battery_value
        imap_dict[new_key] = type_id
        imap_dict.setdefault(item_name, 0)
        purch_dict[item_name] = 1
        added_count += 1

    force_shop_state(root_data["runStats"])
    return added_count


def calculate_item_totals(root_data):
    purch_dict = root_data.get("itemsPurchased", {})
    total_qty = sum(int(value) for value in purch_dict.values())
    unique_qty = sum(1 for value in purch_dict.values() if int(value) > 0)
    return total_qty, unique_qty
