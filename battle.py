import pygame
import copy
import random
from player import Player
from enemy import Enemy


class Battle:
    def __init__(self, start_hp=None):
        self.font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 44)

        self.player = Player()
        if start_hp is not None:
            self.player.hp = max(1, min(start_hp, self.player.max_hp))

        self.enemy = Enemy()

        self.turn = "player"
        self.message = "Player Turn"
        self.undo_stack = []

        self.hand_y = 375
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

        self.card_animations = []
        self.waiting_draw_count = 0
        self.draw_delay = 0

        self.damage_popup = None
        self.damage_popup_timer = 0
        self.damage_popup_target = None

        self.hit_effect = None
        self.hit_effect_timer = 0

        self.player.start_turn(draw_now=False)
        self.start_draw_animation(5)

    def save_state(self):
        self.undo_stack.append(copy.deepcopy((
            self.player,
            self.enemy,
            self.turn,
            self.message
        )))

    def undo(self):
        if self.undo_stack and not self.animating:
            self.player, self.enemy, self.turn, self.message = self.undo_stack.pop()
            self.message = "Undo!"

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        mouse_pos = pygame.mouse.get_pos()

        if self.deck_view is not None:
            if self.close_panel_rect.collidepoint(mouse_pos):
                self.deck_view = None
            return

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
                    self.start_card_animation(i)
                    return

        if self.end_turn_rect.collidepoint(mouse_pos):
            self.end_player_turn()

        elif self.undo_rect.collidepoint(mouse_pos):
            self.undo()

    def start_card_animation(self, index):
        if index >= len(self.player.hand):
            return

        card = self.player.hand[index]

        if self.player.energy < card.cost:
            self.message = "Not enough energy"
            return

        self.save_state()

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

        card.use(self.player, self.enemy)
        used_card = self.player.hand.pop(self.pending_card_index)

        if card.damage > 0:
            self.damage_popup = f"-{card.damage}"
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

        if self.enemy.hp <= 0:
            self.enemy.hp = 0
            self.message = "Victory!"

        self.pending_card = None
        self.pending_card_index = None
        self.animation_type = "card_to_discard"

    def end_player_turn(self):
        if self.animating or self.turn != "player":
            return

        self.save_state()

        for card in self.player.hand:
            self.animate_card_move(
                (card.rect.x, card.rect.y),
                (self.discard_deck_rect.x, self.discard_deck_rect.y),
                card,
                "discard"
            )

        self.player.hand = []

        self.turn = "enemy"
        self.message = "Enemy Turn"
        self.animating = True
        self.animation_type = "discard_hand"

    def finish_discard_hand(self):
        self.animation_timer = 35
        self.animation_type = "enemy_attack"

    def finish_enemy_animation(self):
        before_hp = self.player.hp
        before_block = self.player.block

        self.enemy.take_turn(self.player)

        actual_damage = max(0, before_hp - self.player.hp)

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

        self.hit_effect_timer = 25
        self.damage_popup_timer = 35

        if self.player.hp <= 0:
            self.player.hp = 0
            self.message = "Defeat..."
            self.animating = False
            return

        self.turn = "player"
        self.player.start_turn(draw_now=False)
        self.start_draw_animation(5)

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

            self.card_animations.remove(anim)

    def update(self):
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

    def draw_hp_bar(self, screen, x, y, width, height, hp, max_hp):
        ratio = max(0, hp) / max_hp

        pygame.draw.rect(screen, (60, 60, 60), (x, y, width, height))
        pygame.draw.rect(screen, (200, 40, 40), (x, y, width * ratio, height))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 2)

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

        self.draw_text(screen, "Player", x - 35, y + 85)

    def draw_enemy(self, screen):
        x = 800
        y = 260

        if self.animation_type == "enemy_attack":
            x -= 25

        pygame.draw.circle(screen, (180, 50, 50), (x, y), 70)
        pygame.draw.circle(screen, (40, 20, 20), (x - 25, y - 18), 9)
        pygame.draw.circle(screen, (40, 20, 20), (x + 25, y - 18), 9)
        pygame.draw.rect(screen, (50, 20, 20), (x - 32, y + 22, 64, 14))

        self.draw_text(screen, "Enemy", x - 32, y + 85)

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

        if rect.collidepoint(mouse_x, mouse_y) and not self.animating and self.deck_view is None:
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

        self.draw_text(screen, f"Player HP {self.player.hp}/{self.player.max_hp}", 50, 60)
        self.draw_hp_bar(screen, 50, 100, 250, 30, self.player.hp, self.player.max_hp)
        self.draw_text(screen, f"Block {self.player.block}", 50, 140)

        self.draw_text(screen, f"Enemy HP {self.enemy.hp}/{self.enemy.max_hp}", 700, 60)
        self.draw_hp_bar(screen, 700, 100, 250, 30, self.enemy.hp, self.enemy.max_hp)
        self.draw_text(screen, "Intent: Attack 8", 740, 140)

        self.draw_player(screen)
        self.draw_enemy(screen)

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
