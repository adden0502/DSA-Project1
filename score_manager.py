import json
import heapq
from pathlib import Path


class ScoreManager:
    def __init__(self, player_name="Player"):
        self.player_name = player_name
        self.score = 0

        self.floor_reached = 1
        self.rooms_cleared = 0
        self.monsters_killed = 0
        self.bosses_killed = 0
        self.special_rooms = 0
        self.total_turns = 0
        self.undo_used = 0
        self.rest_used = 0

        self.score_log = []

    def add_score(self, amount, reason):
        self.score += amount
        self.score_log.append({
            "reason": reason,
            "amount": amount,
            "total": self.score
        })

    def reach_floor(self, floor):
        if floor > self.floor_reached:
            self.floor_reached = floor
            self.add_score(500, f"Reached floor {floor}")

    def clear_room(self, room_type):
        self.rooms_cleared += 1
        self.add_score(100, f"Cleared {room_type} room")

        if room_type in ["TREASURE", "EVENT", "REST"]:
            self.special_rooms += 1
            self.add_score(80, f"Visited special room: {room_type}")

        if room_type == "REST":
            self.rest_used += 1
            self.add_score(-20, "Used rest room")

    def clear_battle(self, enemies_defeated, is_boss, turns_used, remaining_hp):
        self.rooms_cleared += 1
        self.add_score(100, "Cleared battle room")

        if is_boss:
            self.bosses_killed += 1
            self.add_score(500, "Defeated boss")
        else:
            self.monsters_killed += enemies_defeated
            self.add_score(50 * enemies_defeated, f"Defeated {enemies_defeated} monster(s)")

        self.total_turns += turns_used
        turn_bonus = max(0, 100 - turns_used * 10)
        self.add_score(turn_bonus, f"Turn bonus: cleared in {turns_used} turn(s)")

        hp_bonus = remaining_hp * 5
        self.add_score(hp_bonus, f"Remaining HP bonus: {remaining_hp} HP")

    def use_undo(self):
        self.undo_used += 1
        self.add_score(-30, "Used undo")

    def build_record(self, defeated=False):
        return {
            "name": self.player_name,
            "score": self.score,
            "floor": self.floor_reached,
            "rooms": self.rooms_cleared,
            "monsters": self.monsters_killed,
            "bosses": self.bosses_killed,
            "turns": self.total_turns,
            "undos": self.undo_used,
            "defeated": defeated,
            "log": self.score_log
        }


class Leaderboard:
    def __init__(self, path="leaderboard.json"):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return []

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

        if not isinstance(data, list):
            return []

        return data

    def save(self, records):
        # Heap-based top-k leaderboard.
        # This satisfies the Leaderboard requirement using heapq.nlargest.
        top_records = heapq.nlargest(
            10,
            records,
            key=lambda item: item.get("score", 0)
        )

        self.path.write_text(
            json.dumps(top_records, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

    def add_record(self, record):
        records = self.load()
        records.append(record)
        self.save(records)
