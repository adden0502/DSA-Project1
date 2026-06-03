import pygame
from battle import Battle
from map_screen import DungeonMap

pygame.init()

screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Card Roguelike Prototype")

clock = pygame.time.Clock()

scene = "map"
dungeon_map = DungeonMap()
battle = None

player_max_hp = 80
player_hp = 80

continue_rect = pygame.Rect(395, 430, 210, 55)


def draw_victory_overlay(screen):
    overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont(None, 52)
    small_font = pygame.font.SysFont(None, 30)

    title = font.render("Victory!", True, (255, 255, 255))
    screen.blit(title, (500 - title.get_width() // 2, 320))

    pygame.draw.rect(screen, (80, 120, 180), continue_rect, border_radius=12)
    pygame.draw.rect(screen, (240, 240, 255), continue_rect, 2, border_radius=12)

    text = small_font.render("Continue Map", True, (255, 255, 255))
    screen.blit(
        text,
        (
            continue_rect.centerx - text.get_width() // 2,
            continue_rect.centery - text.get_height() // 2
        )
    )


def resolve_non_battle_room(room_type):
    global player_hp

    old_floor = dungeon_map.floor

    if room_type == "TREASURE":
        dungeon_map.message = "Treasure room cleared! You found a reward."
        dungeon_map.complete_current_node()

    elif room_type == "REST":
        player_hp = min(player_max_hp, player_hp + 20)
        dungeon_map.message = "Rest room cleared! HP recovered."
        dungeon_map.complete_current_node()

    elif room_type == "EVENT":
        dungeon_map.message = "Event room cleared! Strange event happened."
        dungeon_map.complete_current_node()

    elif room_type == "START":
        dungeon_map.message = "Started the run."
        dungeon_map.complete_current_node()

    if dungeon_map.floor != old_floor:
        player_hp = player_max_hp


running = True
while running:
    screen.fill((22, 22, 28))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if scene == "map":
            room_type = dungeon_map.handle_event(event)

            if room_type in ["MONSTER", "BOSS"]:
                battle = Battle(start_hp=player_hp)
                scene = "battle"

            elif room_type is not None:
                resolve_non_battle_room(room_type)

        elif scene == "battle":
            if battle.enemy.hp <= 0:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if continue_rect.collidepoint(pygame.mouse.get_pos()):
                        player_hp = battle.player.hp

                        old_floor = dungeon_map.floor
                        dungeon_map.complete_current_node()

                        if dungeon_map.floor != old_floor:
                            player_hp = player_max_hp

                        battle = None
                        scene = "map"
            else:
                battle.handle_event(event)

    if scene == "map":
        dungeon_map.player_hp = player_hp
        dungeon_map.player_max_hp = player_max_hp
        dungeon_map.draw(screen)

    elif scene == "battle":
        battle.update()
        battle.draw(screen)

        if battle.enemy.hp <= 0:
            draw_victory_overlay(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
