import random


ITEMS = {
    "Iron Ring": {
        "rarity": "Common",
        "desc": "Max HP +10",
        "max_hp": 10
    },
    "Wooden Shield": {
        "rarity": "Common",
        "desc": "Start each battle with +5 Block",
        "start_block": 5
    },
    "Energy Crystal": {
        "rarity": "Common",
        "desc": "Max Energy +1",
        "max_energy": 1
    },
    "Sharp Blade": {
        "rarity": "Common",
        "desc": "Attack cards deal +2 damage",
        "attack_bonus": 2
    },
    "Blood Amulet": {
        "rarity": "Rare",
        "desc": "Recover 3 HP after winning a battle",
        "battle_heal": 3
    },
    "Battle Manual": {
        "rarity": "Rare",
        "desc": "Draw 1 extra card at the start of battle",
        "extra_draw": 1
    },
    "Reinforced Armor": {
        "rarity": "Rare",
        "desc": "Block cards give +3 Block",
        "block_bonus": 3
    },
    "Lucky Coin": {
        "rarity": "Rare",
        "desc": "Treasure rooms offer 4 items",
        "treasure_choices": 1
    },
    "Phoenix Feather": {
        "rarity": "Epic",
        "desc": "Once per run, revive at 50% HP",
        "revive": True
    },
    "Time Fragment": {
        "rarity": "Epic",
        "desc": "Undo no longer reduces score",
        "free_undo": True
    },
    "Soul Crystal": {
        "rarity": "Epic",
        "desc": "After defeating a boss, Max HP +15",
        "boss_max_hp": 15
    },
    "Berserker Crest": {
        "rarity": "Epic",
        "desc": "At 50% HP or lower, attack cards deal +50%",
        "berserker": True
    },
    "Crown of Kings": {
        "rarity": "Legendary",
        "desc": "Attack cards deal +10 damage",
        "attack_bonus": 10
    },
    "Heart of the Colossus": {
        "rarity": "Legendary",
        "desc": "Max HP +50",
        "max_hp": 50
    },
    "Watcher's Hourglass": {
        "rarity": "Legendary",
        "desc": "Start each battle with +2 Energy this turn",
        "start_energy": 2
    },
    "King's Crown": {
        "rarity": "Boss",
        "desc": "Boss relic: start each battle with +1 Energy this turn",
        "start_energy": 1
    },
    "Soul Staff": {
        "rarity": "Boss",
        "desc": "Boss relic: recover 6 HP after winning a battle",
        "battle_heal": 6
    },
    "Colossus Heart": {
        "rarity": "Boss",
        "desc": "Boss relic: Max HP +30",
        "max_hp": 30
    },
    "Demon Core": {
        "rarity": "Boss",
        "desc": "Boss relic: attack cards deal +5 damage",
        "attack_bonus": 5
    },
    "Hourglass of Eternity": {
        "rarity": "Boss",
        "desc": "Boss relic: Undo no longer reduces score",
        "free_undo": True
    },
    "Broken Timeline": {
        "rarity": "Boss",
        "desc": "Boss relic: using Undo heals 5 HP and gives +1 Energy",
        "undo_heal": 5,
        "undo_energy": 1
    },
}


RARITY_WEIGHTS = {
    "Common": 60,
    "Rare": 25,
    "Epic": 12,
    "Legendary": 3
}


BOSS_DROPS = {
    "Goblin King": "King's Crown",
    "Necromancer Lord": "Soul Staff",
    "Iron Colossus": "Colossus Heart",
    "Twin Flame Demon": "Demon Core",
    "Twin Frost Demon": "Demon Core",
    "Time Watcher": "Hourglass of Eternity",
    "The Undoer": "Broken Timeline",
}


class Inventory:
    def __init__(self):
        self.items = []
        self.phoenix_used = False

    def has(self, item_name):
        return item_name in self.items

    def add(self, item_name):
        if item_name not in ITEMS:
            return False

        self.items.append(item_name)
        return True

    def total_effect(self, key):
        total = 0
        for item_name in self.items:
            total += ITEMS[item_name].get(key, 0)
        return total

    def has_effect(self, key):
        for item_name in self.items:
            if ITEMS[item_name].get(key):
                return True
        return False

    def get_item_desc(self, item_name):
        info = ITEMS.get(item_name, {})
        return info.get("desc", "")

    def get_item_rarity(self, item_name):
        info = ITEMS.get(item_name, {})
        return info.get("rarity", "Unknown")

    def build_rarity_tree(self):
        # Tree-like inventory organization:
        # Inventory
        #   ├─ Common
        #   ├─ Rare
        #   ├─ Epic
        #   ├─ Legendary
        #   └─ Boss
        tree = {
            "Inventory": {
                "Common": [],
                "Rare": [],
                "Epic": [],
                "Legendary": [],
                "Boss": []
            }
        }

        for item_name in self.items:
            rarity = self.get_item_rarity(item_name)

            if rarity not in tree["Inventory"]:
                tree["Inventory"][rarity] = []

            tree["Inventory"][rarity].append(item_name)

        return tree

    def get_summary_lines(self):
        if not self.items:
            return ["No items"]

        tree = self.build_rarity_tree()
        lines = []

        for rarity, item_names in tree["Inventory"].items():
            if not item_names:
                continue

            lines.append(f"[{rarity}]")

            for item in item_names:
                lines.append(f"  - {item}: {self.get_item_desc(item)}")

        return lines


def get_random_item(exclude=None):
    if exclude is None:
        exclude = []

    pool = [
        name for name, info in ITEMS.items()
        if info.get("rarity") in RARITY_WEIGHTS and name not in exclude
    ]

    if not pool:
        return None

    weights = [RARITY_WEIGHTS[ITEMS[name]["rarity"]] for name in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def get_treasure_choices(inventory, count=3):
    choices = []
    exclude = list(inventory.items)

    while len(choices) < count:
        item = get_random_item(exclude + choices)

        if item is None:
            break

        choices.append(item)

    return choices


def get_boss_drop(enemy_types):
    for enemy_type in enemy_types:
        if enemy_type in BOSS_DROPS:
            return BOSS_DROPS[enemy_type]

    return None
