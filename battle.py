import pygame
import copy
import random
from collections import deque
from player import Player
from enemy import Enemy


class Battle:
    def __init__(self, start_hp=None, enemy_types=None, floor=1, is_boss=False):
        self.font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 44)

        self.player = Player()
        if start_hp is not None:
            self.player.hp = max(1, min(start_hp, self.player.max_hp))

        if enemy_types is None:
            if is_boss:
                enemy_types = self.get_boss_types_for_floor(floor)
            else:
                enemy_types = [None]

        self.enemies = [Enemy(enemy_type) for enemy_type in enemy_types]
        self.enemy = self.enemies[0]

        if "Necromancer Lord" in enemy_types:
            self.enemies.append(Enemy("Skeleton"))
            self.enemies.append(Enemy("Skeleton"))

        # Queue-based turn management.
        # The active side is always taken from the front of this queue.
        self.turn_queue = deque(["player", "enemy"])
        self.turn = self.turn_queue[0]
        self.message = "Player Turn"
        self.undo_stack = []

        self.hand_y = 450
        self.card_w = 135
        self.card_h = 180
        self.card_gap = 6
        self.hand_start_x = (1000 - (5 * self.card_w + 4 * self.card_gap)) // 2

        self.end_turn_rect = pygame.Rect(830, 645, 135, 40)
        self.undo_rect = pygame.Rect(690, 645, 120, 40)
        self.all_cards_rect = pygame.Rect(825, 25, 140, 38)

        self.draw_deck_rect = pygame.Rect(35, 520, 90, 120)
        self.discard_deck_rect = pygame.Rect(875, 520, 90, 120)

        self.deck_view = None
        self.close_panel_rect = pygame.Rect(745, 115, 35, 35)

        self.animating = False
        self.animation_timer = 0
        self.animation_type = None
        self.pending_card = None
        self.pending_card_index = None

        self.dragging_card = None
        self.dragging_card_index = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.drag_x = 0
        self.drag_y = 0
        self.drag_start_y = 0
        self.self_cast_threshold = 55
        self.enemy_rect = pygame.Rect(720, 190, 160, 160)
        self.target_enemy = None

        self.card_animations = []
        self.waiting_draw_count = 0
        self.draw_delay = 0

        self.damage_popup = None
        self.damage_popup_timer = 0
        self.damage_popup_target = None

        self.hit_effect = None
        self.hit_effect_timer = 0

        self.initial_state = None
        self.action_log = []
        self.undo_events = []
        self.undo_event = None
        self.undo_wait = 0
        self.undo_restore_enemy = None

        self.pending_before = None

        self.player.start_turn(draw_now=False)
        self.start_draw_animation(5)


    def get_boss_types_for_floor(self, floor):
        boss_table = {
            1: ["Goblin King"],
            2: ["Necromancer Lord"],
            3: ["Iron Colossus"],
            4: ["Twin Flame Demon", "Twin Frost Demon"],
            5: ["Time Watcher"],
        }

        return boss_table.get(floor, ["The Undoer"])


    def sync_turn_from_queue(self):
        self.turn = self.turn_queue[0]

    def advance_turn_queue(self):
        self.turn_queue.rotate(-1)
        self.sync_turn_from_queue()


    def save_state(self):
        self.undo_stack.append(copy.deepcopy((
            self.player,
            self.enemies,
            self.turn,
            self.message
        )))

    def undo(self):
        if self.animating:
            return

        if self.initial_state is None:
            return

        if len(self.action_log) == 0:
            self.player, restored_enemies, self.turn, self.message = copy.deepcopy(self.initial_state)

            if isinstance(restored_enemies, list):
                self.enemies = restored_enemies
            else:
                self.enemies = [restored_enemies]

            if not isinstance(self.enemies, list):
                self.enemies = [self.enemies]

            self.enemy = self.enemies[0] if self.enemies else None
            self.turn_queue = deque([self.turn, "enemy" if self.turn == "player" else "player"])
            self.message = "Already at battle start"
            return

        self.undo_events = list(reversed(self.action_log))
        self.action_log = []

        self.card_animations = []
        self.undo_event = None
        self.undo_wait = 0
        self.undo_restore_enemy = None

        self.animating = True
        self.animation_type = "undo_replay"
        self.message = "Rewinding actions..."

    def handle_event(self, event):
        if self.deck_view is not None:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.close_panel_rect.collidepoint(pygame.mouse.get_pos()):
                    self.deck_view = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if self.draw_deck_rect.collidepoint(mouse_pos):
                self.deck_view = "draw"
                return

            if self.discard_deck_rect.collidepoint(mouse_pos):
                self.deck_view = "discard"
                return

            if self.all_cards_rect.collidepoint(mouse_pos):
                self.deck_view = "all"
                return

            if self.animating:
                return

            if self.turn == "player":
                for i, card in enumerate(self.player.hand):
                    if card.rect and card.rect.collidepoint(mouse_pos):
                        self.dragging_card = card
                        self.dragging_card_index = i
                        self.drag_offset_x = mouse_pos[0] - card.rect.x
                        self.drag_offset_y = mouse_pos[1] - card.rect.y
                        self.drag_x = card.rect.x
                        self.drag_y = card.rect.y
                        self.drag_start_y = card.rect.y

                        if card.damage > 0:
                            self.message = "Drag attack card to an enemy"
                        else:
                            self.message = "Drag upward and release to use"

                        return

            if self.end_turn_rect.collidepoint(mouse_pos):
                self.end_player_turn()

            elif self.undo_rect.collidepoint(mouse_pos):
                self.undo()

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_card is not None:
                mouse_pos = pygame.mouse.get_pos()
                self.drag_x = mouse_pos[0] - self.drag_offset_x
                self.drag_y = mouse_pos[1] - self.drag_offset_y

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging_card is None:
                return

            mouse_pos = pygame.mouse.get_pos()
            card = self.dragging_card
            index = self.dragging_card_index

            if card.damage > 0:
                target = self.get_enemy_at_pos(mouse_pos)

                if target is not None:
                    self.target_enemy = target
                    self.dragging_card = None
                    self.dragging_card_index = None
                    self.start_card_animation(index)
                else:
                    self.message = "Attack card needs a target"
                    self.dragging_card = None
                    self.dragging_card_index = None

            else:
                moved_up = self.drag_start_y - self.drag_y

                if moved_up >= self.self_cast_threshold:
                    self.dragging_card = None
                    self.dragging_card_index = None
                    self.start_card_animation(index)
                else:
                    self.message = "Move the card upward to use it"
                    self.dragging_card = None
                    self.dragging_card_index = None

    def start_card_animation(self, index):
        if index >= len(self.player.hand):
            return

        card = self.player.hand[index]

        if self.player.energy < card.cost:
            self.message = "Not enough energy"
            return

        self.save_state()

        if card.damage > 0 and self.target_enemy is None:
            self.target_enemy = self.enemies[0] if self.enemies else None

        target = self.target_enemy if self.target_enemy is not None else self.enemy

        self.pending_before = {
            "player_hp": self.player.hp,
            "player_block": self.player.block,
            "player_energy": self.player.energy,
            "enemy_hp": target.hp if target is not None else 0,
            "enemy_block": target.block if target is not None else 0,
            "hand_index": index
        }

        self.animating = True
        self.animation_timer = 20
        self.pending_card = card
        self.pending_card_index = index

        if card.damage > 0:
            self.animation_type = "player_attack"
            self.message = f"{card.name}!"
        elif card.block > 0:
            self.animation_type = "player_block"
            self.message = f"{card.name}!"
        else:
            self.animation_type = "card"

    def finish_card_animation(self):
        card = self.pending_card

        target = self.target_enemy if self.target_enemy is not None else self.enemy
        card.use(self.player, target)
        used_card = self.player.hand.pop(self.pending_card_index)

        self.action_log.append({
            "type": "play_card",
            "card": used_card,
            "target": target,
            "before": self.pending_before,
            "after_player_hp": self.player.hp,
            "after_player_block": self.player.block,
            "after_player_energy": self.player.energy,
            "after_enemy_hp": target.hp if "target" in locals() and target is not None else 0,
            "after_enemy_block": target.block if "target" in locals() and target is not None else 0
        })

        if card.damage > 0:
            actual = getattr(card, "last_actual_damage", card.damage)
            blocked = getattr(card, "last_blocked_damage", 0)

            if blocked > 0 and actual == 0:
                self.damage_popup = "BLOCK"
            elif blocked > 0 and actual > 0:
                self.damage_popup = f"-{actual}"
                self.message = f"{blocked} blocked!"
            else:
                self.damage_popup = f"-{actual}"

            self.damage_popup_timer = 35
            self.damage_popup_target = "enemy"

        if card.block > 0:
            self.message = f"Gained {card.block} block"
        else:
            self.message = f"Dealt {card.damage} damage"

        self.animate_card_move(
            (used_card.rect.x, used_card.rect.y),
            (self.discard_deck_rect.x, self.discard_deck_rect.y),
            used_card,
            "discard"
        )

        defeated_target = target
        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]
        self.enemy = self.enemies[0] if self.enemies else defeated_target

        if len(self.enemies) == 0:
            if self.enemy is not None:
                self.enemy.hp = 0
            self.message = "Victory!"

        self.pending_card = None
        self.pending_card_index = None
        self.pending_before = None
        self.target_enemy = None
        self.animation_type = "card_to_discard"

    def end_player_turn(self):
        if self.animating or self.turn != "player":
            return

        self.save_state()

        discarded_cards = list(self.player.hand)
        self.action_log.append({
            "type": "discard_hand",
            "cards": discarded_cards,
            "turn_before": self.turn
        })

        for card in self.player.hand:
            self.animate_card_move(
                (card.rect.x, card.rect.y),
                (self.discard_deck_rect.x, self.discard_deck_rect.y),
                card,
                "discard"
            )

        self.player.hand = []

        self.advance_turn_queue()
        self.message = "Enemy Turn"
        self.animating = True
        self.animation_type = "discard_hand"

    def finish_discard_hand(self):
        self.animation_timer = 35
        self.animation_type = "enemy_attack"

    def finish_enemy_animation(self):
        total_damage = 0
        before_hp = self.player.hp
        before_block = self.player.block
        summaries = []

        for enemy in list(self.enemies):
            if enemy.hp <= 0:
                continue

            result = enemy.take_turn(self.player, self.enemies)
            total_damage += result.get("damage", 0)

            if result.get("message"):
                summaries.append(f"{enemy.get_display_name()}: {result['message']}")
            elif result.get("summoned") is not None:
                summaries.append(f"{enemy.get_display_name()} summoned")
            elif result.get("block", 0) > 0 and result.get("damage", 0) > 0:
                summaries.append(f"{enemy.get_display_name()} attacked and blocked")
            elif result.get("block", 0) > 0:
                summaries.append(f"{enemy.get_display_name()} gained block")
            elif result.get("strength", 0) > 0:
                summaries.append(f"{enemy.get_display_name()} grew stronger")
            elif result.get("damage", 0) > 0:
                summaries.append(f"{enemy.get_display_name()} dealt {result['damage']}")

        actual_damage = max(0, before_hp - self.player.hp)

        self.action_log.append({
            "type": "enemy_attack",
            "enemy_action": "multi_enemy_turn",
            "before_hp": before_hp,
            "before_block": before_block,
            "after_hp": self.player.hp,
            "after_block": self.player.block
        })

        if before_block > 0 and actual_damage == 0:
            self.hit_effect = "blocked"
            self.damage_popup = "BLOCK"
            self.damage_popup_target = "player"
            self.message = "Blocked!"

        elif before_block > 0 and actual_damage > 0:
            self.hit_effect = "guard_break"
            self.damage_popup = f"-{actual_damage}"
            self.damage_popup_target = "player"
            self.message = "Guard broken!"

        else:
            self.hit_effect = "hit"
            self.damage_popup = f"-{actual_damage}"
            self.damage_popup_target = "player"
            self.message = "Hit!"

        if summaries:
            self.message = " / ".join(summaries[:2])

        self.hit_effect_timer = 25
        self.damage_popup_timer = 35

        if self.player.hp <= 0:
            self.player.hp = 0
            self.message = "Defeat..."
            self.animating = False
            return

        self.advance_turn_queue()
        self.player.start_turn(draw_now=False)
        self.start_draw_animation(5)


    def get_boss_types_for_floor(self, floor):
        boss_table = {
            1: ["Goblin King"],
            2: ["Necromancer Lord"],
            3: ["Iron Colossus"],
            4: ["Twin Flame Demon", "Twin Frost Demon"],
            5: ["Time Watcher"],
        }

        return boss_table.get(floor, ["The Undoer"])


    def start_draw_animation(self, count=5):
        self.waiting_draw_count = count
        self.draw_delay = 0
        self.animating = True
        self.animation_type = "draw_cards"
        self.message = "Drawing cards..."

    def animate_card_move(self, start_pos, end_pos, card, target):
        self.card_animations.append({
            "x": start_pos[0],
            "y": start_pos[1],
            "start_x": start_pos[0],
            "start_y": start_pos[1],
            "end_x": end_pos[0],
            "end_y": end_pos[1],
            "timer": 0,
            "duration": 20,
            "card": card,
            "target": target
        })

    def draw_one_card_with_animation(self):
        if len(self.player.draw_pile) == 0:
            if len(self.player.discard_pile) == 0:
                return

            self.player.draw_pile = self.player.discard_pile
            self.player.discard_pile = []
            random.shuffle(self.player.draw_pile)
            self.message = "Shuffled discard pile!"

        if len(self.player.draw_pile) == 0:
            return

        card = self.player.draw_pile.pop()

        hand_index = len(self.player.hand) + len([
            anim for anim in self.card_animations
            if anim["target"] == "hand"
        ])

        end_pos = self.get_hand_card_pos(hand_index)

        self.animate_card_move(
            (self.draw_deck_rect.x, self.draw_deck_rect.y),
            end_pos,
            card,
            "hand"
        )

        if self.initial_state is not None:
            self.action_log.append({
                "type": "draw_card",
                "card": card
            })

    def update_card_animations(self):
        for anim in self.card_animations:
            anim["timer"] += 1
            t = anim["timer"] / anim["duration"]

            if t > 1:
                t = 1

            anim["x"] = anim["start_x"] + (anim["end_x"] - anim["start_x"]) * t
            anim["y"] = anim["start_y"] + (anim["end_y"] - anim["start_y"]) * t

        finished = [
            anim for anim in self.card_animations
            if anim["timer"] >= anim["duration"]
        ]

        for anim in finished:
            if anim["target"] == "hand":
                self.player.hand.append(anim["card"])

            elif anim["target"] == "discard":
                self.player.discard_pile.append(anim["card"])

            elif anim["target"] == "undo_hand":
                self.player.hand.append(anim["card"])

            elif anim["target"] == "undo_draw":
                self.player.draw_pile.append(anim["card"])

            elif anim["target"] == "undo_ignore":
                pass

            self.card_animations.remove(anim)

    def remove_card_from_zones(self, card):
        if card in self.player.hand:
            self.player.hand.remove(card)
            return "hand"

        if card in self.player.discard_pile:
            self.player.discard_pile.remove(card)
            return "discard"

        if card in self.player.draw_pile:
            self.player.draw_pile.remove(card)
            return "draw"

        return None

    def card_current_pos(self, card):
        if card.rect:
            return (card.rect.x, card.rect.y)

        if card in self.player.discard_pile:
            return (self.discard_deck_rect.x, self.discard_deck_rect.y)

        if card in self.player.draw_pile:
            return (self.draw_deck_rect.x, self.draw_deck_rect.y)

        return (500, 360)

    def start_next_undo_event(self):
        if len(self.undo_events) == 0:
            self.player, restored_enemies, self.turn, self.message = copy.deepcopy(self.initial_state)

            if isinstance(restored_enemies, list):
                self.enemies = restored_enemies
            else:
                self.enemies = [restored_enemies]

            if not isinstance(self.enemies, list):
                self.enemies = [self.enemies]

            self.enemy = self.enemies[0] if self.enemies else None
            self.turn_queue = deque([self.turn, "enemy" if self.turn == "player" else "player"])
            self.card_animations = []
            self.undo_event = None
            self.undo_restore_enemy = None
            self.animating = False
            self.animation_type = None
            self.message = "Returned to battle start"
            return

        event = self.undo_events.pop(0)
        self.undo_event = event
        self.card_animations = []

        if event["type"] == "draw_card":
            card = event["card"]
            start_pos = self.card_current_pos(card)
            self.remove_card_from_zones(card)

            self.animate_card_move(
                start_pos,
                (self.draw_deck_rect.x, self.draw_deck_rect.y),
                card,
                "undo_draw"
            )

            for anim in self.card_animations:
                anim["duration"] = 24

            self.message = "Undo: card returns to draw pile"

        elif event["type"] == "play_card":
            card = event["card"]
            before = event["before"]
            target = event.get("target", self.enemy)

            if target is not None:
                if target not in self.enemies:
                    self.enemies.append(target)

                target.hp = max(1, event.get("after_enemy_hp", target.hp))
                target.block = event.get("after_enemy_block", target.block)
                self.enemy = self.enemies[0] if self.enemies else target

                self.undo_restore_enemy = {
                    "target": target,
                    "hp": before["enemy_hp"],
                    "block": before["enemy_block"],
                    "amount": max(0, before["enemy_hp"] - event.get("after_enemy_hp", 0))
                }

            start_pos = self.card_current_pos(card)
            self.remove_card_from_zones(card)

            end_pos = self.get_hand_card_pos(before["hand_index"])

            self.animate_card_move(
                start_pos,
                end_pos,
                card,
                "undo_hand"
            )

            for anim in self.card_animations:
                anim["duration"] = 28

            self.player.energy = before["player_energy"]
            self.player.block = before["player_block"]
            self.turn = "player"
            self.turn_queue = deque(["player", "enemy"])

            self.message = f"Undo: {card.name}"

        elif event["type"] == "discard_hand":
            cards = list(event["cards"])

            for i, card in enumerate(cards):
                if card in self.player.discard_pile:
                    self.player.discard_pile.remove(card)

                self.animate_card_move(
                    (self.discard_deck_rect.x, self.discard_deck_rect.y),
                    self.get_hand_card_pos(i),
                    card,
                    "undo_hand"
                )

            for anim in self.card_animations:
                anim["duration"] = 26

            self.turn = "player"
            self.turn_queue = deque(["player", "enemy"])
            self.message = "Undo: hand returns"

        elif event["type"] == "enemy_attack":
            self.player.hp = event["before_hp"]
            self.player.block = event["before_block"]
            recovered = max(0, event["before_hp"] - event["after_hp"])

            if recovered > 0:
                self.damage_popup = f"+{recovered}"
                self.damage_popup_target = "player"
                self.damage_popup_timer = 30

            self.hit_effect = "blocked" if event["before_block"] > 0 else None
            self.hit_effect_timer = 20
            self.undo_wait = 28
            self.turn = "enemy"
            self.turn_queue = deque(["enemy", "player"])
            self.message = "Undo: enemy attack reversed"

    def update_undo_replay(self):
        if self.undo_event is None:
            self.start_next_undo_event()
            return

        if len(self.card_animations) > 0:
            self.update_card_animations()
            return

        if self.undo_restore_enemy is not None:
            target = self.undo_restore_enemy["target"]
            target.hp = self.undo_restore_enemy["hp"]
            target.block = self.undo_restore_enemy["block"]

            amount = self.undo_restore_enemy.get("amount", 0)
            if amount > 0:
                self.damage_popup = f"+{amount}"
                self.damage_popup_target = "enemy"
                self.damage_popup_timer = 30

            self.undo_restore_enemy = None
            self.undo_wait = 18
            return

        if self.undo_wait > 0:
            self.undo_wait -= 1
            return

        self.undo_event = None

    def update(self):
        if self.animation_type == "undo_replay":
            self.update_undo_replay()

            if self.damage_popup_timer > 0:
                self.damage_popup_timer -= 1

            if self.hit_effect_timer > 0:
                self.hit_effect_timer -= 1

            return

        if self.animation_type == "draw_cards":
            self.draw_delay -= 1

            if self.waiting_draw_count > 0 and self.draw_delay <= 0:
                self.draw_one_card_with_animation()
                self.waiting_draw_count -= 1
                self.draw_delay = 8

            self.update_card_animations()

            if self.waiting_draw_count == 0 and len(self.card_animations) == 0:
                self.animating = False
                self.animation_type = None
                self.message = "Player Turn"

                if self.initial_state is None:
                    self.initial_state = copy.deepcopy((
                        self.player,
                        self.enemies,
                        self.turn,
                        self.message
                    ))

            if self.hit_effect_timer > 0:
                self.hit_effect_timer -= 1

            if self.damage_popup_timer > 0:
                self.damage_popup_timer -= 1

            return

        if self.animation_type == "card_to_discard":
            self.update_card_animations()

            if len(self.card_animations) == 0:
                self.animating = False
                self.animation_type = None

            return

        if self.animation_type == "discard_hand":
            self.update_card_animations()

            if len(self.card_animations) == 0:
                self.finish_discard_hand()

            return

        if self.animating:
            self.animation_timer -= 1

            if self.animation_timer <= 0:
                if self.animation_type in ["player_attack", "player_block", "card"]:
                    self.finish_card_animation()

                elif self.animation_type == "enemy_attack":
                    self.finish_enemy_animation()

        if self.damage_popup_timer > 0:
            self.damage_popup_timer -= 1

        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= 1

    def get_hand_card_pos(self, index):
        return (
            self.hand_start_x + index * (self.card_w + self.card_gap),
            self.hand_y
        )

    def get_card_count_dict(self, cards):
        result = {}

        for card in cards:
            if card.name not in result:
                result[card.name] = {
                    "count": 0,
                    "cost": card.cost,
                    "damage": card.damage,
                    "block": card.block
                }

            result[card.name]["count"] += 1

        return result

    def get_all_cards(self):
        anim_cards = [anim["card"] for anim in self.card_animations]
        return self.player.draw_pile + self.player.hand + self.player.discard_pile + anim_cards

    def draw_text(self, screen, text, x, y, font=None, color=(230, 230, 230)):
        if font is None:
            font = self.font

        img = font.render(text, True, color)
        screen.blit(img, (x, y))

    def draw_shield_icon(self, screen, x, y, value, size=20):
        points = [
            (x, y - size),
            (x + int(size * 0.8), y - int(size * 0.45)),
            (x + int(size * 0.6), y + int(size * 0.75)),
            (x, y + size),
            (x - int(size * 0.6), y + int(size * 0.75)),
            (x - int(size * 0.8), y - int(size * 0.45)),
        ]

        pygame.draw.polygon(screen, (70, 140, 220), points)
        pygame.draw.polygon(screen, (220, 240, 255), points, 2)

        block_text = self.small_font.render(str(value), True, (255, 255, 255))
        screen.blit(
            block_text,
            (
                x - block_text.get_width() // 2,
                y - block_text.get_height() // 2
            )
        )

    def draw_hp_bar(self, screen, x, y, width, height, hp, max_hp):
        ratio = max(0, hp) / max_hp

        pygame.draw.rect(screen, (60, 60, 60), (x, y, width, height))
        pygame.draw.rect(screen, (200, 40, 40), (x, y, int(width * ratio), height))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 2)

        if height < 20:
            hp_font = self.small_font
        else:
            hp_font = self.font

        hp_text = hp_font.render(f"{hp}/{max_hp}", True, (255, 255, 255))

        screen.blit(
            hp_text,
            (
                x + width // 2 - hp_text.get_width() // 2,
                y + height // 2 - hp_text.get_height() // 2
            )
        )

    def draw_player(self, screen):
        x = 180
        y = 260

        if self.animation_type == "player_attack":
            x += 25

        pygame.draw.circle(screen, (80, 130, 230), (x, y), 50)
        pygame.draw.circle(screen, (230, 230, 255), (x, y - 15), 18)
        pygame.draw.rect(screen, (60, 90, 180), (x - 32, y + 20, 64, 55), border_radius=10)

        if self.animation_type == "player_block":
            pygame.draw.circle(screen, (120, 180, 255), (x, y), 75, 5)

        if self.hit_effect_timer > 0:
            if self.hit_effect == "blocked":
                pygame.draw.circle(screen, (120, 180, 255), (x, y), 85, 6)
                pygame.draw.circle(screen, (180, 220, 255), (x, y), 65, 3)

            elif self.hit_effect == "guard_break":
                pygame.draw.circle(screen, (255, 220, 80), (x, y), 85, 5)
                pygame.draw.line(screen, (255, 220, 80), (x - 55, y - 55), (x + 55, y + 55), 4)
                pygame.draw.line(screen, (255, 220, 80), (x + 55, y - 55), (x - 55, y + 55), 4)

            elif self.hit_effect == "hit":
                pygame.draw.circle(screen, (255, 80, 80), (x, y), 85, 5)
                pygame.draw.line(screen, (255, 80, 80), (x - 65, y), (x + 65, y), 5)

        

    def draw_intent_icon(self, screen, enemy, x, y):
        intent = getattr(enemy, "intent", "")
        value = getattr(enemy, "intent_value", 0)

        icon_x = x
        icon_y = y - 92

        if intent in ["Attack", "Heavy Attack", "Dark Strike", "Big Slam", "Dark Bolt", "King Slash", "Death Bolt", "Slam", "Earthquake", "Fireball", "Inferno", "Strike", "Time Echo", "Reverse Strike"]:
            color = (210, 70, 70)
            border = (255, 210, 210)
            label = str(value)

            pygame.draw.circle(screen, color, (icon_x, icon_y), 25)
            pygame.draw.circle(screen, border, (icon_x, icon_y), 25, 3)

            # simple sword shape
            pygame.draw.line(screen, (255, 255, 255), (icon_x - 9, icon_y + 9), (icon_x + 8, icon_y - 8), 4)
            pygame.draw.line(screen, (255, 255, 255), (icon_x - 12, icon_y + 3), (icon_x - 4, icon_y + 11), 3)

            value_img = self.small_font.render(label, True, (255, 255, 255))
            badge_rect = pygame.Rect(icon_x + 32, icon_y - 14, value_img.get_width() + 14, 28)
            pygame.draw.rect(screen, (25, 25, 35), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 240), badge_rect, 2, border_radius=8)
            screen.blit(
                value_img,
                (
                    badge_rect.centerx - value_img.get_width() // 2,
                    badge_rect.centery - value_img.get_height() // 2
                )
            )

        elif intent in ["Defend", "Royal Guard", "Fortify", "Guard", "Ice Shield", "Frozen Armor"]:
            color = (70, 140, 220)
            border = (220, 240, 255)
            label = str(value)

            points = [
                (icon_x, icon_y - 26),
                (icon_x + 20, icon_y - 10),
                (icon_x + 16, icon_y + 18),
                (icon_x, icon_y + 28),
                (icon_x - 16, icon_y + 18),
                (icon_x - 20, icon_y - 10),
            ]

            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, border, points, 3)

            value_img = self.small_font.render(label, True, (255, 255, 255))
            badge_rect = pygame.Rect(icon_x + 32, icon_y - 14, value_img.get_width() + 14, 28)
            pygame.draw.rect(screen, (25, 25, 35), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 240), badge_rect, 2, border_radius=8)
            screen.blit(
                value_img,
                (
                    badge_rect.centerx - value_img.get_width() // 2,
                    badge_rect.centery - value_img.get_height() // 2
                )
            )

        elif intent == "Shield Bash":
            color = (120, 100, 210)
            border = (235, 230, 255)
            label = str(value)

            pygame.draw.circle(screen, color, (icon_x, icon_y), 25)
            pygame.draw.circle(screen, border, (icon_x, icon_y), 25, 3)

            pygame.draw.line(screen, (255, 255, 255), (icon_x - 10, icon_y + 8), (icon_x + 8, icon_y - 8), 4)
            pygame.draw.polygon(
                screen,
                (180, 220, 255),
                [
                    (icon_x - 5, icon_y - 18),
                    (icon_x + 9, icon_y - 8),
                    (icon_x + 6, icon_y + 10),
                    (icon_x - 5, icon_y + 16),
                    (icon_x - 16, icon_y + 10),
                    (icon_x - 18, icon_y - 8),
                ]
            )

            value_img = self.small_font.render(label, True, (255, 255, 255))
            badge_rect = pygame.Rect(icon_x + 32, icon_y - 14, value_img.get_width() + 14, 28)
            pygame.draw.rect(screen, (25, 25, 35), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 240), badge_rect, 2, border_radius=8)
            screen.blit(
                value_img,
                (
                    badge_rect.centerx - value_img.get_width() // 2,
                    badge_rect.centery - value_img.get_height() // 2
                )
            )

        elif intent in ["Ritual", "Royal Command", "Dark Ritual", "Army of Darkness", "Future Sight"]:
            color = (150, 70, 190)
            border = (240, 210, 255)
            label = f"+{value}"

            pygame.draw.circle(screen, color, (icon_x, icon_y), 25)
            pygame.draw.circle(screen, border, (icon_x, icon_y), 25, 3)

            # star-like buff icon
            pygame.draw.polygon(
                screen,
                (255, 255, 255),
                [
                    (icon_x, icon_y - 17),
                    (icon_x + 5, icon_y - 5),
                    (icon_x + 17, icon_y - 5),
                    (icon_x + 7, icon_y + 3),
                    (icon_x + 11, icon_y + 16),
                    (icon_x, icon_y + 8),
                    (icon_x - 11, icon_y + 16),
                    (icon_x - 7, icon_y + 3),
                    (icon_x - 17, icon_y - 5),
                    (icon_x - 5, icon_y - 5),
                ]
            )

            value_img = self.small_font.render(label, True, (255, 255, 255))
            badge_rect = pygame.Rect(icon_x + 32, icon_y - 14, value_img.get_width() + 14, 28)
            pygame.draw.rect(screen, (25, 25, 35), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 240), badge_rect, 2, border_radius=8)
            screen.blit(
                value_img,
                (
                    badge_rect.centerx - value_img.get_width() // 2,
                    badge_rect.centery - value_img.get_height() // 2
                )
            )

        elif intent in ["Summon", "Reinforcements", "Raise Dead"]:
            color = (90, 60, 150)
            border = (230, 220, 255)
            label = "+1"

            pygame.draw.circle(screen, color, (icon_x, icon_y), 25)
            pygame.draw.circle(screen, border, (icon_x, icon_y), 25, 3)

            # small skull/summon icon
            pygame.draw.circle(screen, (245, 245, 245), (icon_x, icon_y - 4), 12)
            pygame.draw.rect(screen, (245, 245, 245), (icon_x - 9, icon_y + 5, 18, 12))
            pygame.draw.circle(screen, (30, 20, 40), (icon_x - 5, icon_y - 5), 3)
            pygame.draw.circle(screen, (30, 20, 40), (icon_x + 5, icon_y - 5), 3)

            value_img = self.small_font.render(label, True, (255, 255, 255))
            badge_rect = pygame.Rect(icon_x + 32, icon_y - 14, value_img.get_width() + 14, 28)
            pygame.draw.rect(screen, (25, 25, 35), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 240), badge_rect, 2, border_radius=8)
            screen.blit(
                value_img,
                (
                    badge_rect.centerx - value_img.get_width() // 2,
                    badge_rect.centery - value_img.get_height() // 2
                )
            )

        elif intent in ["Armor Crush", "Rewind", "Temporal Collapse", "Time Stop", "Grand Rewind", "Reversed Heal", "Undo Reality"]:
            color = (180, 120, 60)
            border = (255, 230, 190)
            label = str(value) if value else "!"

            pygame.draw.circle(screen, color, (icon_x, icon_y), 25)
            pygame.draw.circle(screen, border, (icon_x, icon_y), 25, 3)

            # clock / special icon
            pygame.draw.circle(screen, (255, 255, 255), (icon_x, icon_y), 12, 3)
            pygame.draw.line(screen, (255, 255, 255), (icon_x, icon_y), (icon_x, icon_y - 8), 3)
            pygame.draw.line(screen, (255, 255, 255), (icon_x, icon_y), (icon_x + 7, icon_y + 4), 3)

            value_img = self.small_font.render(label, True, (255, 255, 255))
            badge_rect = pygame.Rect(icon_x + 32, icon_y - 14, value_img.get_width() + 14, 28)
            pygame.draw.rect(screen, (25, 25, 35), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 240), badge_rect, 2, border_radius=8)
            screen.blit(
                value_img,
                (
                    badge_rect.centerx - value_img.get_width() // 2,
                    badge_rect.centery - value_img.get_height() // 2
                )
            )

        else:
            pygame.draw.circle(screen, (90, 90, 110), (icon_x, icon_y), 25)
            pygame.draw.circle(screen, (230, 230, 240), (icon_x, icon_y), 25, 3)
            q_img = self.font.render("?", True, (255, 255, 255))
            screen.blit(q_img, (icon_x - q_img.get_width() // 2, icon_y - q_img.get_height() // 2))

    def get_enemy_position(self, index, total):
        if total == 1:
            return 800, 260

        spacing = 145
        start_x = 800 - (total - 1) * spacing // 2
        return start_x + index * spacing, 260

    def get_enemy_at_pos(self, pos):
        for enemy in reversed(self.enemies):
            if enemy.rect and enemy.rect.collidepoint(pos):
                return enemy

        return None

    def draw_enemy(self, screen, enemy, index=0, total=1):
        x, y = self.get_enemy_position(index, total)

        if self.animation_type == "enemy_attack":
            x -= 18

        enemy.rect = pygame.Rect(x - 65, y - 70, 130, 145)

        is_hovered = (
            self.dragging_card is not None
            and enemy.rect.collidepoint(pygame.mouse.get_pos())
        )

        if is_hovered:
            pygame.draw.circle(screen, (255, 90, 90), (x, y), 76, 5)

        self.draw_intent_icon(screen, enemy, x, y)

        if enemy.enemy_type in ["Necromancer", "Necromancer Lord"]:
            body_color = (90, 50, 150)
        elif enemy.enemy_type == "Skeleton":
            body_color = (205, 205, 190)
        elif enemy.enemy_type == "Shield Guard":
            body_color = (90, 110, 150)
        elif enemy.enemy_type == "Cultist":
            body_color = (120, 60, 140)
        elif enemy.enemy_type == "Slime":
            body_color = (80, 170, 90)
        elif enemy.enemy_type == "Goblin King":
            body_color = (200, 90, 55)
        elif enemy.enemy_type == "Iron Colossus":
            body_color = (120, 120, 125)
        elif enemy.enemy_type == "Twin Flame Demon":
            body_color = (220, 70, 40)
        elif enemy.enemy_type == "Twin Frost Demon":
            body_color = (80, 150, 220)
        elif enemy.enemy_type == "Time Watcher":
            body_color = (140, 70, 210)
        elif enemy.enemy_type == "The Undoer":
            body_color = (40, 40, 70)
        else:
            body_color = (180, 50, 50)

        pygame.draw.circle(screen, body_color, (x, y), 55)
        pygame.draw.circle(screen, (40, 20, 20), (x - 20, y - 15), 7)
        pygame.draw.circle(screen, (40, 20, 20), (x + 20, y - 15), 7)
        pygame.draw.rect(screen, (50, 20, 20), (x - 25, y + 20, 50, 12))

        name = enemy.get_display_name() if hasattr(enemy, "get_display_name") else "Enemy"
        if getattr(enemy, "is_boss", False):
            name = f"{name} P{getattr(enemy, 'phase', 1)}"

        self.draw_text(screen, name, x - 65, y + 68, self.small_font)
        self.draw_hp_bar(screen, x - 55, y + 105, 110, 22, enemy.hp, enemy.max_hp)

        if getattr(enemy, "block", 0) > 0:
            self.draw_shield_icon(
                screen,
                x + 78,
                y + 116,
                enemy.block,
                13
            )

        # Enemy intent is displayed as an icon above the enemy.

    def draw_energy(self, screen):
        center = (80, 455)
        radius = 34

        pygame.draw.circle(screen, (40, 90, 180), center, radius)
        pygame.draw.circle(screen, (255, 255, 255), center, radius, 3)

        energy_text = self.big_font.render(
            f"{self.player.energy}/{self.player.max_energy}",
            True,
            (255, 255, 255)
        )

        screen.blit(
            energy_text,
            (
                center[0] - energy_text.get_width() // 2,
                center[1] - energy_text.get_height() // 2
            )
        )

    def draw_card(self, screen, card, x, y, index):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        rect = pygame.Rect(x, y, self.card_w, self.card_h)

        if rect.collidepoint(mouse_x, mouse_y) and not self.animating and self.deck_view is None and card is not self.dragging_card:
            rect.y -= 18

        card.rect = rect

        if card.damage > 0:
            card_color = (240, 205, 195)
            card_type = "ATTACK"
            effect_lines = [f"Deal {card.damage}", "damage"]
            symbol = "ATK"

        elif card.block > 0:
            card_color = (195, 220, 245)
            card_type = "SKILL"
            effect_lines = [f"Gain {card.block}", "block"]
            symbol = "DEF"

        else:
            card_color = (220, 220, 220)
            card_type = "CARD"
            effect_lines = ["No effect"]
            symbol = "ETC"

        pygame.draw.rect(screen, card_color, rect, border_radius=12)
        pygame.draw.rect(screen, (30, 30, 30), rect, 3, border_radius=12)

        pygame.draw.circle(screen, (40, 90, 180), (rect.x + 25, rect.y + 25), 21)
        pygame.draw.circle(screen, (255, 255, 255), (rect.x + 25, rect.y + 25), 21, 2)

        cost_text = self.big_font.render(str(card.cost), True, (255, 255, 255))
        screen.blit(
            cost_text,
            (
                rect.x + 25 - cost_text.get_width() // 2,
                rect.y + 25 - cost_text.get_height() // 2
            )
        )

        self.draw_text(screen, card.name, rect.x + 52, rect.y + 18, self.font, (20, 20, 20))
        self.draw_text(screen, card_type, rect.x + 15, rect.y + 58, self.small_font, (80, 80, 80))

        pygame.draw.rect(screen, (245, 245, 245), (rect.x + 25, rect.y + 80, 84, 34), border_radius=8)
        pygame.draw.rect(screen, (70, 70, 70), (rect.x + 25, rect.y + 80, 84, 34), 2, border_radius=8)
        self.draw_text(screen, symbol, rect.x + 51, rect.y + 88, self.font, (20, 20, 20))

        pygame.draw.line(screen, (80, 80, 80), (rect.x + 15, rect.y + 125), (rect.x + 120, rect.y + 125), 2)

        for i, line in enumerate(effect_lines):
            self.draw_text(
                screen,
                line,
                rect.x + 22,
                rect.y + 136 + i * 22,
                self.font,
                (20, 20, 20)
            )

    def draw_deck_pile(self, screen, rect, count, label):
        pygame.draw.rect(screen, (70, 70, 90), rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 230), rect, 3, border_radius=8)

        for i in range(3):
            pygame.draw.rect(
                screen,
                (85, 85, 110),
                (rect.x + 6 + i * 3, rect.y + 6 + i * 3, rect.width - 12, rect.height - 12),
                2,
                border_radius=8
            )

        count_text = self.big_font.render(str(count), True, (240, 240, 255))
        screen.blit(
            count_text,
            (
                rect.centerx - count_text.get_width() // 2,
                rect.centery - count_text.get_height() // 2
            )
        )

        label_text = self.small_font.render(label, True, (230, 230, 240))
        screen.blit(
            label_text,
            (
                rect.centerx - label_text.get_width() // 2,
                rect.y - 25
            )
        )

    def draw_buttons(self, screen):
        pygame.draw.rect(screen, (70, 80, 120), self.all_cards_rect, border_radius=10)
        self.draw_text(screen, "All Cards", self.all_cards_rect.x + 20, self.all_cards_rect.y + 10)

        pygame.draw.rect(screen, (80, 80, 80), self.undo_rect, border_radius=10)
        self.draw_text(screen, "Undo", self.undo_rect.x + 38, self.undo_rect.y + 10)

        pygame.draw.rect(screen, (180, 120, 40), self.end_turn_rect, border_radius=10)
        self.draw_text(screen, "End Turn", self.end_turn_rect.x + 22, self.end_turn_rect.y + 10)

    def draw_deck_view_panel(self, screen):
        if self.deck_view is None:
            return

        overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(220, 100, 560, 470)
        pygame.draw.rect(screen, (35, 35, 50), panel, border_radius=15)
        pygame.draw.rect(screen, (230, 230, 240), panel, 3, border_radius=15)

        pygame.draw.rect(screen, (130, 60, 60), self.close_panel_rect, border_radius=8)
        self.draw_text(screen, "X", self.close_panel_rect.x + 10, self.close_panel_rect.y + 6, self.font)

        if self.deck_view == "draw":
            title = "Draw Pile"
            cards = self.player.draw_pile
        elif self.deck_view == "discard":
            title = "Discard Pile"
            cards = self.player.discard_pile
        else:
            title = "All Cards"
            cards = self.get_all_cards()

        self.draw_text(screen, title, 250, 125, self.big_font)
        self.draw_text(screen, f"Total: {len(cards)}", 250, 170, self.font)

        counts = self.get_card_count_dict(cards)

        y = 220
        if len(counts) == 0:
            self.draw_text(screen, "No cards", 250, y, self.font, (230, 230, 230))
            return

        for name, info in counts.items():
            line = f"{name} x{info['count']}  | Cost {info['cost']}"
            if info["damage"] > 0:
                line += f" | Deal {info['damage']}"
            if info["block"] > 0:
                line += f" | Block {info['block']}"

            self.draw_text(screen, line, 250, y, self.font, (230, 230, 230))
            y += 35

    def draw(self, screen):
        pygame.draw.rect(screen, (35, 35, 60), (320, 20, 360, 60), border_radius=15)
        self.draw_text(screen, self.turn.upper() + " TURN", 400, 35, self.big_font)

        
        self.draw_hp_bar(screen, 50, 100, 250, 30, self.player.hp, self.player.max_hp)
        if self.player.block > 0:
            self.draw_shield_icon(
                screen,
                325,
                115,
                self.player.block,
                18
            )

        self.draw_player(screen)

        for enemy_index, enemy in enumerate(self.enemies):
            self.draw_enemy(screen, enemy, enemy_index, len(self.enemies))

        self.draw_text(screen, self.message, 420, 220)

        if self.damage_popup and self.damage_popup_timer > 0:
            if self.damage_popup_target == "player":
                popup_x, popup_y = 170, 230
            else:
                popup_x, popup_y = 780, 230

            if self.damage_popup == "BLOCK":
                popup_color = (120, 200, 255)
            else:
                popup_color = (255, 80, 80)

            self.draw_text(
                screen,
                self.damage_popup,
                popup_x,
                popup_y - (35 - self.damage_popup_timer),
                self.big_font,
                popup_color
            )

        for i, card in enumerate(self.player.hand):
            if self.dragging_card is not None and i == self.dragging_card_index:
                continue

            x, y = self.get_hand_card_pos(i)
            self.draw_card(screen, card, x, y, i)

        for anim in self.card_animations:
            self.draw_card(
                screen,
                anim["card"],
                anim["x"],
                anim["y"],
                0
            )

        if self.dragging_card is not None:
            if self.dragging_card.damage > 0:
                line_color = (255, 120, 120)
                pygame.draw.line(
                    screen,
                    line_color,
                    (
                        int(self.drag_x + self.card_w // 2),
                        int(self.drag_y + self.card_h // 2)
                    ),
                    pygame.mouse.get_pos(),
                    3
                )
            else:
                moved_up = self.drag_start_y - self.drag_y

                if moved_up >= self.self_cast_threshold:
                    hint_color = (120, 210, 255)
                    hint_text = "Release to use"
                else:
                    hint_color = (160, 160, 180)
                    hint_text = "Move upward"

                pygame.draw.line(
                    screen,
                    hint_color,
                    (
                        int(self.drag_x + self.card_w // 2),
                        int(self.drag_start_y + self.card_h // 2)
                    ),
                    (
                        int(self.drag_x + self.card_w // 2),
                        int(self.drag_y + self.card_h // 2)
                    ),
                    3
                )

                self.draw_text(
                    screen,
                    hint_text,
                    int(self.drag_x),
                    int(self.drag_y - 28),
                    self.small_font,
                    hint_color
                )

            self.draw_card(
                screen,
                self.dragging_card,
                self.drag_x,
                self.drag_y,
                self.dragging_card_index
            )

        self.draw_deck_pile(
            screen,
            self.draw_deck_rect,
            len(self.player.draw_pile),
            "DRAW"
        )

        self.draw_deck_pile(
            screen,
            self.discard_deck_rect,
            len(self.player.discard_pile),
            "DISCARD"
        )

        self.draw_energy(screen)
        self.draw_buttons(screen)
        self.draw_deck_view_panel(screen)
