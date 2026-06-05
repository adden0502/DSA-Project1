import pygame
from battle import Battle
from map_screen import DungeonMap
from score_manager import ScoreManager, Leaderboard
from item_system import Inventory, ITEMS, get_treasure_choices, get_boss_drop

pygame.init()

screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Card Roguelike Prototype")

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 58)

scene = "title"
dungeon_map = None
battle = None
score_manager = None
leaderboard = Leaderboard()
inventory = Inventory()

player_name = ""
player_max_hp = 80
player_hp = 80

current_room_type = None
current_battle_is_boss = False
battle_turns = 0
battle_enemy_count = 0
current_enemy_types = []

treasure_choices = []
event_options = []
reward_title = ""

start_rect = pygame.Rect(390, 300, 220, 55)
leaderboard_rect = pygame.Rect(390, 370, 220, 55)
quit_rect = pygame.Rect(390, 440, 220, 55)
continue_rect = pygame.Rect(395, 430, 210, 55)
back_rect = pygame.Rect(390, 610, 220, 45)
skip_reward_rect = pygame.Rect(390, 580, 220, 45)
items_button_rect = pygame.Rect(835, 25, 130, 38)
close_items_rect = pygame.Rect(745, 95, 35, 35)
show_items_panel = False
inventory_scroll = 0


def draw_text(text, x, y, used_font=None, color=(235, 235, 235)):
    if used_font is None:
        used_font = font
    img = used_font.render(text, True, color)
    screen.blit(img, (x, y))


def draw_centered(text, y, used_font=None, color=(235, 235, 235)):
    if used_font is None:
        used_font = font
    img = used_font.render(text, True, color)
    screen.blit(img, (500 - img.get_width() // 2, y))


def draw_button(rect, text, color=(70, 80, 120)):
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, (230, 230, 240), rect, 2, border_radius=12)
    img = font.render(text, True, (255, 255, 255))
    screen.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - img.get_height() // 2))


def reset_run():
    global dungeon_map, battle, score_manager, player_hp, player_max_hp, inventory
    global current_room_type, current_battle_is_boss, battle_turns, battle_enemy_count
    global current_enemy_types, treasure_choices, event_options, reward_title, show_items_panel, inventory_scroll

    dungeon_map = DungeonMap()
    battle = None
    inventory = Inventory()
    player_max_hp = 80
    player_hp = player_max_hp
    score_manager = ScoreManager(player_name if player_name.strip() else "Player")

    current_room_type = None
    current_battle_is_boss = False
    battle_turns = 0
    battle_enemy_count = 0
    current_enemy_types = []
    treasure_choices = []
    event_options = []
    reward_title = ""
    show_items_panel = False
    inventory_scroll = 0
inventory_scroll = 0


def apply_item_immediate_effect(item_name):
    global player_max_hp, player_hp

    info = ITEMS.get(item_name, {})

    if info.get("max_hp", 0) > 0:
        amount = info["max_hp"]
        player_max_hp += amount
        player_hp += amount

    if info.get("boss_max_hp", 0) > 0:
        amount = info["boss_max_hp"]
        player_max_hp += amount
        player_hp += amount


def apply_inventory_to_battle(battle):
    if battle is None:
        return

    # Prevent repeated relic application from stacking every frame.
    # Item effects should be applied once when a battle starts.
    if getattr(battle, "inventory_applied", False):
        return

    battle.inventory_applied = True

    battle.player.max_hp = player_max_hp
    battle.player.hp = min(player_hp, player_max_hp)

    if not hasattr(battle.player, "base_max_energy"):
        battle.player.base_max_energy = battle.player.max_energy

    energy_bonus = inventory.total_effect("max_energy")
    battle.player.max_energy = battle.player.base_max_energy + energy_bonus
    battle.player.energy = battle.player.max_energy

    battle.player.block += inventory.total_effect("start_block")
    battle.player.energy += inventory.total_effect("start_energy")

    attack_bonus = inventory.total_effect("attack_bonus")
    block_bonus = inventory.total_effect("block_bonus")

    if inventory.has_effect("berserker") and battle.player.hp <= battle.player.max_hp // 2:
        berserker = True
    else:
        berserker = False

    for pile in [battle.player.draw_pile, battle.player.hand, battle.player.discard_pile]:
        for card in pile:
            if not hasattr(card, "base_damage"):
                card.base_damage = card.damage
            if not hasattr(card, "base_block"):
                card.base_block = card.block

            card.damage = card.base_damage
            card.block = card.base_block

            if card.damage > 0:
                card.damage += attack_bonus
                if berserker:
                    card.damage = int(card.damage * 1.5)

            if card.block > 0:
                card.block += block_bonus


def apply_after_battle_rewards(is_boss):
    global player_hp

    heal = inventory.total_effect("battle_heal")
    if heal > 0:
        player_hp = min(player_max_hp, player_hp + heal)

    if is_boss and inventory.total_effect("boss_max_hp") > 0:
        # Soul Crystal style effect is handled only once through item pickup for simplicity.
        pass


def draw_title():
    draw_centered("CARD ROGUELIKE", 130, big_font)
    draw_centered("Enter your name before starting", 210, small_font, (190, 190, 210))

    name_box = pygame.Rect(330, 240, 340, 42)
    pygame.draw.rect(screen, (35, 35, 50), name_box, border_radius=8)
    pygame.draw.rect(screen, (230, 230, 240), name_box, 2, border_radius=8)

    shown_name = player_name if player_name else "Type name..."
    color = (255, 255, 255) if player_name else (140, 140, 150)
    draw_text(shown_name, name_box.x + 15, name_box.y + 10, font, color)

    draw_button(start_rect, "Start Game", (80, 130, 90))
    draw_button(leaderboard_rect, "Leaderboard", (70, 80, 120))
    draw_button(quit_rect, "Quit", (120, 70, 70))


def draw_leaderboard():
    draw_centered("LEADERBOARD", 55, big_font)
    records = leaderboard.load()

    if not records:
        draw_centered("No records yet", 160, font, (190, 190, 210))
    else:
        y = 130
        draw_text("Rank", 130, y, small_font, (200, 200, 220))
        draw_text("Name", 210, y, small_font, (200, 200, 220))
        draw_text("Score", 430, y, small_font, (200, 200, 220))
        draw_text("Floor", 560, y, small_font, (200, 200, 220))
        draw_text("Boss", 660, y, small_font, (200, 200, 220))
        draw_text("Undo", 760, y, small_font, (200, 200, 220))
        y += 35

        for i, record in enumerate(records[:10]):
            draw_text(str(i + 1), 140, y, font)
            draw_text(record.get("name", "Player")[:14], 210, y, font)
            draw_text(str(record.get("score", 0)), 430, y, font)
            draw_text(str(record.get("floor", 1)), 570, y, font)
            draw_text(str(record.get("bosses", 0)), 675, y, font)
            draw_text(str(record.get("undos", 0)), 775, y, font)
            y += 40

    draw_button(back_rect, "Back", (80, 80, 100))


def draw_score_breakdown():
    if score_manager is None:
        return

    panel = pygame.Rect(95, 315, 810, 275)
    pygame.draw.rect(screen, (30, 30, 45), panel, border_radius=12)
    pygame.draw.rect(screen, (190, 190, 220), panel, 2, border_radius=12)

    draw_text("Score Breakdown", panel.x + 20, panel.y + 15, font, (240, 240, 255))

    categories = {
        "Floor reached": 0,
        "Room clear": 0,
        "Monster kills": 0,
        "Boss kills": 0,
        "Special rooms": 0,
        "Turn bonus": 0,
        "HP bonus": 0,
        "Undo penalty": 0,
        "Rest penalty": 0,
        "Other": 0
    }

    for log in score_manager.score_log:
        reason = log.get("reason", "")
        amount = log.get("amount", 0)

        if reason.startswith("Reached floor"):
            categories["Floor reached"] += amount
        elif reason.startswith("Cleared battle") or reason.startswith("Cleared ") and reason.endswith("room"):
            categories["Room clear"] += amount
        elif reason.startswith("Defeated ") and "monster" in reason:
            categories["Monster kills"] += amount
        elif reason.startswith("Defeated boss"):
            categories["Boss kills"] += amount
        elif reason.startswith("Visited special room"):
            categories["Special rooms"] += amount
        elif reason.startswith("Turn bonus"):
            categories["Turn bonus"] += amount
        elif reason.startswith("Remaining HP bonus"):
            categories["HP bonus"] += amount
        elif reason.startswith("Used undo"):
            categories["Undo penalty"] += amount
        elif reason.startswith("Used rest room"):
            categories["Rest penalty"] += amount
        else:
            categories["Other"] += amount

    rows = list(categories.items())
    left_x = panel.x + 35
    right_x = panel.x + 420
    start_y = panel.y + 60
    row_gap = 34

    for i, (name, amount) in enumerate(rows):
        x = left_x if i < 5 else right_x
        y = start_y + (i if i < 5 else i - 5) * row_gap

        if amount > 0:
            amount_text = f"+{amount}"
            color = (140, 230, 150)
        elif amount < 0:
            amount_text = str(amount)
            color = (255, 130, 130)
        else:
            amount_text = "0"
            color = (170, 170, 180)

        draw_text(name, x, y, small_font, (230, 230, 235))
        draw_text(amount_text, x + 210, y, small_font, color)

    total_color = (140, 230, 150) if score_manager.score >= 0 else (255, 130, 130)
    draw_text("Total Score", panel.x + 300, panel.y + 245, font, (255, 255, 255))
    draw_text(str(score_manager.score), panel.x + 460, panel.y + 245, font, total_color)


def draw_game_over():
    draw_centered("DEFEAT", 55, big_font, (255, 120, 120))

    if score_manager is not None:
        draw_centered(f"Final Score: {score_manager.score}", 115, font)
        draw_centered(
            f"Floor {score_manager.floor_reached}  |  Rooms {score_manager.rooms_cleared}  |  Bosses {score_manager.bosses_killed}  |  Undo {score_manager.undo_used}",
            150,
            small_font,
            (210, 210, 225)
        )

    draw_score_breakdown()
    draw_button(back_rect, "Back to Title", (80, 80, 120))


def draw_items_button():
    pygame.draw.rect(screen, (70, 80, 120), items_button_rect, border_radius=10)
    pygame.draw.rect(screen, (230, 230, 240), items_button_rect, 2, border_radius=10)

    label = font.render("Items", True, (255, 255, 255))
    screen.blit(
        label,
        (
            items_button_rect.centerx - label.get_width() // 2,
            items_button_rect.centery - label.get_height() // 2
        )
    )


def draw_inventory_panel():
    if not show_items_panel:
        return

    overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(220, 80, 560, 510)
    pygame.draw.rect(screen, (30, 30, 45), panel, border_radius=14)
    pygame.draw.rect(screen, (220, 220, 240), panel, 3, border_radius=14)

    pygame.draw.rect(screen, (130, 60, 60), close_items_rect, border_radius=8)
    draw_text("X", close_items_rect.x + 10, close_items_rect.y + 7, font)

    draw_text("Inventory", panel.x + 25, panel.y + 25, big_font, (255, 255, 255))

    if not inventory.items:
        draw_text("No items yet", panel.x + 30, panel.y + 105, font, (210, 210, 220))
        return

    visible_count = 6
    max_scroll = max(0, len(inventory.items) - visible_count)
    scroll = max(0, min(inventory_scroll, max_scroll))
    visible_items = inventory.items[scroll:scroll + visible_count]

    y = panel.y + 100

    for item_name in visible_items:
        info = ITEMS[item_name]
        rarity = info["rarity"]
        desc = info["desc"]

        if rarity == "Common":
            rarity_color = (210, 210, 210)
        elif rarity == "Rare":
            rarity_color = (120, 180, 255)
        elif rarity == "Epic":
            rarity_color = (190, 130, 255)
        elif rarity == "Legendary":
            rarity_color = (255, 210, 90)
        else:
            rarity_color = (255, 150, 120)

        draw_text(item_name, panel.x + 30, y, font, (255, 255, 255))
        draw_text(f"[{rarity}]", panel.x + 250, y + 2, small_font, rarity_color)

        words = desc.split()
        line = ""
        line_y = y + 28

        for word in words:
            if len(line + " " + word) > 48:
                draw_text(line, panel.x + 30, line_y, small_font, (210, 210, 220))
                line_y += 22
                line = word
            else:
                line = (line + " " + word).strip()

        if line:
            draw_text(line, panel.x + 30, line_y, small_font, (210, 210, 220))

        y += 65

    if len(inventory.items) > visible_count:
        bar_x = panel.right - 24
        bar_y = panel.y + 95
        bar_h = 390
        handle_h = max(45, int(bar_h * visible_count / len(inventory.items)))

        pygame.draw.rect(screen, (65, 65, 85), (bar_x, bar_y, 8, bar_h), border_radius=4)

        if max_scroll > 0:
            handle_y = bar_y + int((bar_h - handle_h) * scroll / max_scroll)
        else:
            handle_y = bar_y

        pygame.draw.rect(screen, (220, 220, 240), (bar_x, handle_y, 8, handle_h), border_radius=4)

        draw_text(
            f"{scroll + 1}-{min(scroll + visible_count, len(inventory.items))} / {len(inventory.items)}",
            panel.x + 30,
            panel.bottom - 35,
            small_font,
            (180, 180, 200)
        )


def draw_reward_screen():
    draw_centered(reward_title, 60, big_font)

    if reward_title == "Treasure":
        draw_centered("Choose one item or skip", 120, small_font, (200, 200, 220))
    elif reward_title == "Boss Reward":
        draw_centered("Choose boss reward or skip", 120, small_font, (200, 200, 220))
    else:
        draw_centered("Choose one event result or skip", 120, small_font, (200, 200, 220))

    for i, item_name in enumerate(treasure_choices):
        rect = pygame.Rect(180 + i * 210, 210, 190, 260)
        pygame.draw.rect(screen, (40, 40, 60), rect, border_radius=12)
        pygame.draw.rect(screen, (230, 230, 240), rect, 2, border_radius=12)

        rarity = ITEMS[item_name]["rarity"]
        desc = ITEMS[item_name]["desc"]

        draw_text(item_name[:16], rect.x + 15, rect.y + 20, font, (255, 255, 255))
        draw_text(rarity, rect.x + 15, rect.y + 55, small_font, (180, 200, 255))

        words = desc.split()
        line = ""
        y = rect.y + 100

        for word in words:
            if len(line + " " + word) > 18:
                draw_text(line, rect.x + 15, y, small_font, (220, 220, 220))
                y += 26
                line = word
            else:
                line = (line + " " + word).strip()

        if line:
            draw_text(line, rect.x + 15, y, small_font, (220, 220, 220))

    if not treasure_choices:
        draw_centered("No more available items", 300, font, (200, 200, 210))

    draw_button(skip_reward_rect, "Skip", (90, 90, 110))


def draw_event_screen():
    draw_centered("Event Room", 60, big_font)
    draw_centered("Choose one result", 120, small_font, (200, 200, 220))

    for i, option in enumerate(event_options):
        rect = pygame.Rect(230, 210 + i * 95, 540, 70)
        pygame.draw.rect(screen, (40, 40, 60), rect, border_radius=12)
        pygame.draw.rect(screen, (230, 230, 240), rect, 2, border_radius=12)

        draw_text(option["title"], rect.x + 20, rect.y + 12, font, (255, 255, 255))
        draw_text(option["desc"], rect.x + 20, rect.y + 42, small_font, (220, 220, 230))


def draw_victory_overlay():
    overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    title = big_font.render("Victory!", True, (255, 255, 255))
    screen.blit(title, (500 - title.get_width() // 2, 320))
    draw_button(continue_rect, "Continue Map", (80, 120, 180))


def is_battle_won(battle):
    if battle is None:
        return False
    if battle.animation_type == "undo_replay":
        return False
    if hasattr(battle, "enemies"):
        return len([enemy for enemy in battle.enemies if enemy.hp > 0]) == 0
    return battle.enemy is not None and battle.enemy.hp <= 0


def is_battle_lost(battle):
    if battle is None:
        return False
    return battle.player.hp <= 0


def save_defeat_score():
    if score_manager is None:
        return
    record = score_manager.build_record(defeated=True)
    leaderboard.add_record(record)


def open_treasure_room(title="Treasure", forced_item=None):
    global scene, treasure_choices, reward_title

    reward_title = title

    if forced_item is not None:
        treasure_choices = [forced_item]
    else:
        count = 3 + inventory.total_effect("treasure_choices")
        treasure_choices = get_treasure_choices(inventory, count=count)

    scene = "reward"


def open_event_room():
    global scene, event_options

    event_options = [
        {
            "title": "Mystic Fountain",
            "desc": "Recover 20 HP.",
            "type": "heal",
            "amount": 20
        },
        {
            "title": "Ancient Blessing",
            "desc": "Max HP +5.",
            "type": "max_hp",
            "amount": 5
        },
        {
            "title": "Suspicious Merchant",
            "desc": "Lose 10 HP, gain a random item.",
            "type": "trade_hp_item",
            "amount": 10
        },
        {
            "title": "Cursed Chest",
            "desc": "Max HP -10, gain a powerful item.",
            "type": "cursed_item",
            "amount": 10
        },
    ]

    scene = "event"


def apply_event_option(option):
    global player_hp, player_max_hp

    option_type = option["type"]
    amount = option["amount"]

    if option_type == "heal":
        player_hp = min(player_max_hp, player_hp + amount)

    elif option_type == "max_hp":
        player_max_hp += amount
        player_hp += amount

    elif option_type == "trade_hp_item":
        player_hp = max(1, player_hp - amount)
        choices = get_treasure_choices(inventory, count=1)
        if choices:
            item_name = choices[0]
            inventory.add(item_name)
            apply_item_immediate_effect(item_name)

    elif option_type == "cursed_item":
        player_max_hp = max(20, player_max_hp - amount)
        player_hp = min(player_hp, player_max_hp)
        choices = get_treasure_choices(inventory, count=1)
        if choices:
            item_name = choices[0]
            inventory.add(item_name)
            apply_item_immediate_effect(item_name)


def complete_current_map_node():
    global player_hp

    old_floor = dungeon_map.floor
    dungeon_map.complete_current_node()

    if dungeon_map.floor != old_floor:
        player_hp = player_max_hp
        score_manager.reach_floor(dungeon_map.floor)


def skip_reward():
    global scene

    if reward_title in ["Treasure", "Boss Reward"]:
        dungeon_map.message = "Skipped reward"
        complete_current_map_node()
        scene = "map"
    else:
        dungeon_map.message = "Skipped reward"
        scene = "map"


def resolve_non_battle_room(room_type):
    global player_hp

    if room_type == "TREASURE":
        score_manager.clear_room("TREASURE")
        open_treasure_room("Treasure")

    elif room_type == "REST":
        player_hp = min(player_max_hp, player_hp + 20)
        dungeon_map.message = "Rest room cleared! HP recovered."
        score_manager.clear_room("REST")
        complete_current_map_node()

    elif room_type == "EVENT":
        score_manager.clear_room("EVENT")
        open_event_room()

    elif room_type == "START":
        dungeon_map.message = "Started the run."
        complete_current_map_node()


running = True
while running:
    screen.fill((22, 22, 28))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if scene == "title":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    reset_run()
                    scene = "map"
                elif len(player_name) < 16 and event.unicode.isprintable():
                    player_name += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if start_rect.collidepoint(mouse_pos):
                    reset_run()
                    scene = "map"
                elif leaderboard_rect.collidepoint(mouse_pos):
                    scene = "leaderboard"
                elif quit_rect.collidepoint(mouse_pos):
                    running = False

        elif scene == "leaderboard":
            if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(pygame.mouse.get_pos()):
                scene = "title"

        elif scene == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(pygame.mouse.get_pos()):
                scene = "title"

        elif scene == "reward":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if skip_reward_rect.collidepoint(mouse_pos):
                    skip_reward()
                    continue

                for i, item_name in enumerate(treasure_choices):
                    rect = pygame.Rect(180 + i * 210, 210, 190, 260)
                    if rect.collidepoint(mouse_pos):
                        inventory.add(item_name)
                        apply_item_immediate_effect(item_name)

                        if reward_title in ["Treasure", "Boss Reward"]:
                            dungeon_map.message = f"Obtained {item_name}"
                            complete_current_map_node()
                            scene = "map"
                        else:
                            dungeon_map.message = f"Obtained {item_name}"
                            scene = "map"
                        break

        elif scene == "event":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for i, option in enumerate(event_options):
                    rect = pygame.Rect(230, 210 + i * 95, 540, 70)
                    if rect.collidepoint(mouse_pos):
                        apply_event_option(option)
                        dungeon_map.message = option["title"]
                        complete_current_map_node()
                        scene = "map"
                        break

        elif scene == "map":
            if show_items_panel and event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(inventory.items) - 6)

                if event.y > 0:
                    inventory_scroll = max(0, inventory_scroll - 1)
                elif event.y < 0:
                    inventory_scroll = min(max_scroll, inventory_scroll + 1)

                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if show_items_panel:
                    if close_items_rect.collidepoint(mouse_pos):
                        show_items_panel = False
                        inventory_scroll = 0
                    continue

                if items_button_rect.collidepoint(mouse_pos):
                    show_items_panel = True
                    inventory_scroll = 0
                    continue

            if show_items_panel:
                continue

            room_type = dungeon_map.handle_event(event)

            if room_type == "MONSTER":
                current_room_type = "MONSTER"
                current_battle_is_boss = False
                battle_turns = 1
                battle = Battle(start_hp=player_hp)
                apply_inventory_to_battle(battle)
                battle_enemy_count = len(battle.enemies)
                current_enemy_types = [enemy.enemy_type for enemy in battle.enemies]
                scene = "battle"

            elif room_type == "BOSS":
                current_room_type = "BOSS"
                current_battle_is_boss = True
                battle_turns = 1
                battle = Battle(start_hp=player_hp, floor=dungeon_map.floor, is_boss=True)
                apply_inventory_to_battle(battle)
                battle_enemy_count = len(battle.enemies)
                current_enemy_types = [enemy.enemy_type for enemy in battle.enemies]
                scene = "battle"

            elif room_type is not None:
                resolve_non_battle_room(room_type)

        elif scene == "battle":
            if is_battle_won(battle):
                if event.type == pygame.MOUSEBUTTONDOWN and continue_rect.collidepoint(pygame.mouse.get_pos()):
                    player_hp = battle.player.hp
                    apply_after_battle_rewards(current_battle_is_boss)

                    score_manager.clear_battle(
                        enemies_defeated=battle_enemy_count,
                        is_boss=current_battle_is_boss,
                        turns_used=battle_turns,
                        remaining_hp=player_hp
                    )

                    if current_battle_is_boss:
                        drop = get_boss_drop(current_enemy_types)
                        if drop is not None:
                            open_treasure_room("Boss Reward", forced_item=drop)
                        else:
                            complete_current_map_node()
                            scene = "map"
                    else:
                        complete_current_map_node()
                        scene = "map"

                    battle = None

            elif is_battle_lost(battle):
                if inventory.has_effect("revive") and not inventory.phoenix_used:
                    inventory.phoenix_used = True
                    battle.player.hp = battle.player.max_hp // 2
                    player_hp = battle.player.hp
                    battle.message = "Phoenix Feather revived you!"
                else:
                    save_defeat_score()
                    scene = "game_over"

            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if battle.undo_rect.collidepoint(pygame.mouse.get_pos()):
                        if not inventory.has_effect("free_undo"):
                            score_manager.use_undo()

                        undo_heal = inventory.total_effect("undo_heal")
                        undo_energy = inventory.total_effect("undo_energy")

                        if undo_heal > 0:
                            battle.player.hp = min(battle.player.max_hp, battle.player.hp + undo_heal)

                        if undo_energy > 0:
                            battle.player.energy += undo_energy

                battle.handle_event(event)

    if scene == "title":
        draw_title()

    elif scene == "leaderboard":
        draw_leaderboard()

    elif scene == "game_over":
        draw_game_over()

    elif scene == "reward":
        draw_reward_screen()

    elif scene == "event":
        draw_event_screen()

    elif scene == "map":
        dungeon_map.player_hp = player_hp
        dungeon_map.player_max_hp = player_max_hp
        dungeon_map.draw(screen)
        draw_items_button()
        draw_inventory_panel()

    elif scene == "battle":
        previous_turn = battle.turn
        battle.update()

        if previous_turn == "enemy" and battle.turn == "player":
            battle_turns += 1

        battle.draw(screen)

        if is_battle_won(battle):
            draw_victory_overlay()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
