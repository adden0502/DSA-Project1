
import random
from collections import deque


class Enemy:
    NORMAL_TYPES = ["Goblin", "Shield Guard", "Cultist", "Slime", "Necromancer"]
    BOSS_TYPES = [
        "Goblin King",
        "Necromancer Lord",
        "Iron Colossus",
        "Twin Flame Demon",
        "Twin Frost Demon",
        "Time Watcher",
        "The Undoer",
    ]

    def __init__(self, enemy_type=None):
        if enemy_type is None:
            enemy_type = random.choice(self.NORMAL_TYPES)

        self.enemy_type = enemy_type
        self.turn_count = 0
        self.block = 0
        self.rect = None
        self.strength = 0
        self.phase = 1
        self.is_boss = enemy_type in self.BOSS_TYPES

        hp_table = {
            "Goblin": 42,
            "Shield Guard": 60,
            "Cultist": 48,
            "Slime": 55,
            "Necromancer": 65,
            "Skeleton": 24,
            "Goblin King": 120,
            "Necromancer Lord": 160,
            "Iron Colossus": 220,
            "Twin Flame Demon": 100,
            "Twin Frost Demon": 100,
            "Time Watcher": 300,
            "The Undoer": 220,
        }

        self.max_hp = hp_table.get(enemy_type, 50)
        self.hp = self.max_hp
        self.intent = "Attack"
        self.intent_value = 8
        self.choose_intent()

    def update_phase(self):
        if self.enemy_type == "Goblin King" and self.hp <= self.max_hp * 0.5:
            self.phase = 2
        elif self.enemy_type == "Necromancer Lord":
            if self.hp <= 40:
                self.phase = 3
            elif self.hp <= 80:
                self.phase = 2
        elif self.enemy_type == "Iron Colossus":
            if self.hp <= 50:
                self.phase = 3
            elif self.hp <= 110:
                self.phase = 2
        elif self.enemy_type == "Time Watcher":
            if self.hp <= 100:
                self.phase = 3
            elif self.hp <= 200:
                self.phase = 2

    def choose_intent(self):
        self.update_phase()

        if self.enemy_type == "Goblin":
            if self.turn_count % 3 == 2:
                self.intent = "Heavy Attack"
                self.intent_value = 12
            else:
                self.intent = "Attack"
                self.intent_value = 7

        elif self.enemy_type == "Shield Guard":
            if self.block <= 0:
                self.intent = "Defend"
                self.intent_value = 10
            elif self.turn_count % 2 == 0:
                self.intent = "Shield Bash"
                self.intent_value = 6
            else:
                self.intent = "Defend"
                self.intent_value = 8

        elif self.enemy_type == "Cultist":
            if self.turn_count % 3 == 0:
                self.intent = "Ritual"
                self.intent_value = 2
            else:
                self.intent = "Dark Strike"
                self.intent_value = 6 + self.strength

        elif self.enemy_type == "Slime":
            roll = random.random()
            if roll < 0.45:
                self.intent = "Attack"
                self.intent_value = 6
            elif roll < 0.75:
                self.intent = "Defend"
                self.intent_value = 7
            else:
                self.intent = "Big Slam"
                self.intent_value = 11

        elif self.enemy_type == "Necromancer":
            if self.turn_count % 3 == 0:
                self.intent = "Summon"
                self.intent_value = 1
            elif self.turn_count % 3 == 1:
                self.intent = "Dark Bolt"
                self.intent_value = 8
            else:
                self.intent = "Defend"
                self.intent_value = 8

        elif self.enemy_type == "Skeleton":
            if self.turn_count % 2 == 0:
                self.intent = "Attack"
                self.intent_value = 5 + self.strength
            else:
                self.intent = "Defend"
                self.intent_value = 5

        elif self.enemy_type == "Goblin King":
            if self.phase == 2:
                pattern = self.turn_count % 3
                if pattern == 0:
                    self.intent = "King Slash"
                    self.intent_value = 25
                elif pattern == 1:
                    self.intent = "Reinforcements"
                    self.intent_value = 2
                else:
                    self.intent = "Royal Guard"
                    self.intent_value = 20
            else:
                pattern = self.turn_count % 4
                if pattern == 0:
                    self.intent = "Royal Command"
                    self.intent_value = 2
                elif pattern == 1:
                    self.intent = "King Slash"
                    self.intent_value = 18
                elif pattern == 2:
                    self.intent = "Reinforcements"
                    self.intent_value = 2
                else:
                    self.intent = "Royal Guard"
                    self.intent_value = 20

        elif self.enemy_type == "Necromancer Lord":
            if self.phase == 3:
                pattern = self.turn_count % 3
                if pattern == 0:
                    self.intent = "Army of Darkness"
                    self.intent_value = 5
                elif pattern == 1:
                    self.intent = "Raise Dead"
                    self.intent_value = 2
                else:
                    self.intent = "Death Bolt"
                    self.intent_value = 18
            elif self.phase == 2:
                pattern = self.turn_count % 3
                if pattern == 0:
                    self.intent = "Raise Dead"
                    self.intent_value = 2
                elif pattern == 1:
                    self.intent = "Dark Ritual"
                    self.intent_value = 2
                else:
                    self.intent = "Death Bolt"
                    self.intent_value = 15
            else:
                pattern = self.turn_count % 3
                if pattern == 0:
                    self.intent = "Summon"
                    self.intent_value = 1
                elif pattern == 1:
                    self.intent = "Dark Ritual"
                    self.intent_value = 2
                else:
                    self.intent = "Death Bolt"
                    self.intent_value = 15

        elif self.enemy_type == "Iron Colossus":
            if self.phase == 3:
                if self.turn_count % 2 == 0:
                    self.intent = "Earthquake"
                    self.intent_value = 40
                else:
                    self.intent = "Armor Crush"
                    self.intent_value = 0
            else:
                pattern = self.turn_count % 4
                if pattern == 0:
                    self.intent = "Fortify"
                    self.intent_value = 25
                elif pattern == 1:
                    self.intent = "Slam"
                    self.intent_value = 20 if self.phase == 1 else 30
                elif pattern == 2:
                    self.intent = "Armor Crush"
                    self.intent_value = 0
                else:
                    self.intent = "Earthquake"
                    self.intent_value = 30 if self.phase == 1 else 35

        elif self.enemy_type == "Twin Flame Demon":
            if self.turn_count % 3 == 2:
                self.intent = "Inferno"
                self.intent_value = 25
            else:
                self.intent = "Fireball"
                self.intent_value = 18

        elif self.enemy_type == "Twin Frost Demon":
            if self.turn_count % 2 == 0:
                self.intent = "Ice Shield"
                self.intent_value = 20
            else:
                self.intent = "Frozen Armor"
                self.intent_value = 10

        elif self.enemy_type == "Time Watcher":
            if self.phase == 3:
                pattern = self.turn_count % 4
                if pattern == 0:
                    self.intent = "Temporal Collapse"
                    self.intent_value = 0
                elif pattern == 1:
                    self.intent = "Time Stop"
                    self.intent_value = 1
                elif pattern == 2:
                    self.intent = "Grand Rewind"
                    self.intent_value = 35
                else:
                    self.intent = "Strike"
                    self.intent_value = 25
            elif self.phase == 2:
                pattern = self.turn_count % 4
                if pattern == 0:
                    self.intent = "Rewind"
                    self.intent_value = 30
                elif pattern == 1:
                    self.intent = "Time Echo"
                    self.intent_value = 12
                elif pattern == 2:
                    self.intent = "Guard"
                    self.intent_value = 20
                else:
                    self.intent = "Strike"
                    self.intent_value = 20
            else:
                pattern = self.turn_count % 3
                if pattern == 0:
                    self.intent = "Strike"
                    self.intent_value = 15
                elif pattern == 1:
                    self.intent = "Guard"
                    self.intent_value = 20
                else:
                    self.intent = "Future Sight"
                    self.intent_value = 10

        elif self.enemy_type == "The Undoer":
            pattern = self.turn_count % 3
            if pattern == 0:
                self.intent = "Reverse Strike"
                self.intent_value = 14
            elif pattern == 1:
                self.intent = "Reversed Heal"
                self.intent_value = 18
            else:
                self.intent = "Undo Reality"
                self.intent_value = 0

    def take_damage(self, damage):
        self.update_phase()

        if self.enemy_type == "Iron Colossus" and self.phase >= 2:
            damage = max(1, damage // 2)

        blocked = min(self.block, damage)
        self.block -= blocked
        actual_damage = damage - blocked
        self.hp -= actual_damage

        if self.hp < 0:
            self.hp = 0

        self.update_phase()
        return actual_damage, blocked

    def gain_block(self, amount):
        self.block += amount

    def attack_player(self, player, damage):
        damage += self.strength
        actual_damage = max(0, damage - player.block)
        player.hp -= actual_damage
        player.block = max(0, player.block - damage)
        return actual_damage

    def summon_enemy(self, enemies, enemy_type, max_count=None):
        if max_count is not None:
            count = sum(1 for enemy in enemies if enemy.enemy_type == enemy_type and enemy.hp > 0)
            if count >= max_count:
                return None

        summoned = Enemy(enemy_type)
        enemies.append(summoned)
        return summoned

    def buff_allies(self, enemies, strength=0, block=0, target_types=None):
        for enemy in enemies:
            if enemy.hp <= 0:
                continue
            if target_types is not None and enemy.enemy_type not in target_types:
                continue
            enemy.strength += strength
            enemy.block += block

    def get_alive_ally_graph(self, enemies):
        # Graph representation for enemy AI.
        # Each living enemy is a node, and nearby screen/order neighbors are edges.
        alive = [enemy for enemy in enemies if enemy.hp > 0]
        graph = {}

        for i, enemy in enumerate(alive):
            neighbors = []

            if i - 1 >= 0:
                neighbors.append(alive[i - 1])

            if i + 1 < len(alive):
                neighbors.append(alive[i + 1])

            graph[enemy] = neighbors

        return graph

    def bfs_nearest_weak_ally(self, enemies):
        # BFS decision support:
        # support-type enemies search the enemy graph for a weak ally.
        if enemies is None or self not in enemies:
            return None

        graph = self.get_alive_ally_graph(enemies)

        if self not in graph:
            return None

        visited = set()
        queue = deque([self])
        visited.add(self)

        while queue:
            current = queue.popleft()

            if current is not self and current.hp <= current.max_hp * 0.4:
                return current

            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return None


    def take_turn(self, player, enemies=None):
        if enemies is None:
            enemies = []

        self.update_phase()
        weak_ally = self.bfs_nearest_weak_ally(enemies)

        result = {
            "action": self.intent,
            "damage": 0,
            "block": 0,
            "strength": 0,
            "summoned": None,
            "message": ""
        }

        if self.enemy_type == "Iron Colossus":
            self.gain_block(10)
            result["block"] += 10

        if self.enemy_type in ["Twin Flame Demon", "Twin Frost Demon"]:
            alive = [enemy.enemy_type for enemy in enemies if enemy.hp > 0]
            if "Twin Flame Demon" not in alive or "Twin Frost Demon" not in alive:
                self.strength = max(self.strength, 12)

        attack_intents = [
            "Attack", "Heavy Attack", "Dark Strike", "Big Slam", "Dark Bolt",
            "King Slash", "Death Bolt", "Slam", "Earthquake", "Fireball",
            "Inferno", "Strike", "Time Echo", "Reverse Strike"
        ]

        if self.intent in attack_intents:
            result["damage"] = self.attack_player(player, self.intent_value)

        elif self.intent in ["Defend", "Royal Guard", "Fortify", "Guard", "Ice Shield"]:
            if weak_ally is not None and self.enemy_type in ["Shield Guard", "Twin Frost Demon", "Necromancer Lord"]:
                weak_ally.gain_block(self.intent_value)
                result["block"] += self.intent_value
                result["message"] = f"BFS protected {weak_ally.get_display_name()}"
            else:
                self.gain_block(self.intent_value)
                result["block"] += self.intent_value

        elif self.intent == "Shield Bash":
            self.gain_block(5)
            result["damage"] = self.attack_player(player, self.intent_value)
            result["block"] += 5

        elif self.intent == "Ritual":
            self.strength += self.intent_value
            result["strength"] = self.intent_value

        elif self.intent == "Summon":
            summoned = self.summon_enemy(enemies, "Skeleton", max_count=2)
            if summoned is not None:
                result["summoned"] = summoned
            else:
                result["damage"] = self.attack_player(player, 7)
                result["action"] = "Dark Bolt"

        elif self.intent == "Royal Command":
            self.buff_allies(enemies, strength=self.intent_value, target_types=["Goblin", "Skeleton"])
            result["strength"] = self.intent_value

        elif self.intent == "Reinforcements":
            for _ in range(2):
                summoned = self.summon_enemy(enemies, "Goblin", max_count=3)
                if summoned is not None and result["summoned"] is None:
                    result["summoned"] = summoned

        elif self.intent == "Dark Ritual":
            self.buff_allies(enemies, strength=self.intent_value, target_types=["Skeleton"])
            result["strength"] = self.intent_value

        elif self.intent == "Raise Dead":
            summoned = self.summon_enemy(enemies, "Skeleton", max_count=3)
            if summoned is not None:
                result["summoned"] = summoned
            else:
                self.gain_block(12)
                result["block"] += 12

        elif self.intent == "Army of Darkness":
            self.buff_allies(enemies, strength=5, block=10, target_types=["Skeleton"])
            result["strength"] = 5
            result["block"] += 10

        elif self.intent == "Armor Crush":
            player.block = 0
            result["message"] = "Player block removed"

        elif self.intent == "Frozen Armor":
            # BFS is used to locate the nearest weak ally, then armor is focused there.
            if weak_ally is not None:
                weak_ally.gain_block(self.intent_value * 2)
                result["block"] += self.intent_value * 2
                result["message"] = f"BFS focused armor on {weak_ally.get_display_name()}"
            else:
                self.buff_allies(enemies, block=self.intent_value)
                result["block"] += self.intent_value

        elif self.intent == "Future Sight":
            self.strength += self.intent_value
            result["strength"] = self.intent_value

        elif self.intent in ["Rewind", "Grand Rewind", "Reversed Heal"]:
            heal_amount = min(self.intent_value, self.max_hp - self.hp)
            self.hp += heal_amount
            if self.intent == "Grand Rewind":
                self.gain_block(20)
                result["block"] += 20
            result["message"] = f"Healed {heal_amount}"

        elif self.intent == "Temporal Collapse":
            player.block = 0
            result["message"] = "Player block removed"

        elif self.intent == "Time Stop":
            if hasattr(player, "energy"):
                player.energy = max(0, player.energy - self.intent_value)
            result["message"] = "Energy reduced"

        elif self.intent == "Undo Reality":
            if hasattr(player, "discard_hand"):
                player.discard_hand()
            result["message"] = "Player hand discarded"

        self.turn_count += 1
        self.choose_intent()
        return result

    def get_display_name(self):
        return self.enemy_type

    def get_intent_text(self):
        return f"{self.intent} {self.intent_value}" if self.intent_value else self.intent
