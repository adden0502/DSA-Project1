import random
import pygame


class MapNode:
    def __init__(self, row, col, lane, x, y, room_type):
        self.row = row
        self.col = col
        self.lane = lane
        self.x = x
        self.y = y
        self.room_type = room_type
        self.next_nodes = []
        self.visited = False
        self.available = False
        self.radius = 24

    def contains(self, pos):
        mx, my = pos
        dx = mx - self.x
        dy = my - self.y
        return dx * dx + dy * dy <= self.radius * self.radius


class DungeonMap:
    def __init__(self):
        self.font = pygame.font.SysFont(None, 26)
        self.big_font = pygame.font.SysFont(None, 42)

        self.nodes = []
        self.current_node = None
        self.selected_node = None
        self.floor = 1
        self.player_hp = 80
        self.player_max_hp = 80
        self.message = "Choose a connected room"

        self.generate_map()

    def generate_map(self):
        self.nodes = []

        self.rows = 7

        # Lane-based map.
        # 왼쪽/오른쪽으로 조금씩 갈라지지만, 모든 연결은 위쪽 행으로만 향한다.
        lane_x = [150, 280, 410, 540, 670, 800]
        y_positions = [620, 535, 450, 365, 280, 195, 115]

        # 각 행에 존재할 lane을 미리 정한다.
        # START는 아래 중앙, BOSS는 위 중앙.
        row_lanes = [
            [2],
            [1, 2, 3, 4],
            [1, 2, 3, 4],
            [0, 1, 2, 3, 4, 5],
            [0, 1, 2, 3, 4, 5],
            [1, 2, 3, 4],
            [3],
        ]

        for row in range(self.rows):
            row_nodes = []

            for col, lane in enumerate(row_lanes[row]):
                x = lane_x[lane] + random.randint(-8, 8)
                y = y_positions[row] + random.randint(-5, 5)

                if row == 0:
                    room_type = "START"
                elif row == self.rows - 1:
                    room_type = "BOSS"
                else:
                    room_type = random.choices(
                        ["MONSTER", "TREASURE", "EVENT", "REST"],
                        weights=[55, 15, 20, 10]
                    )[0]

                row_nodes.append(MapNode(row, col, lane, x, y, room_type))

            self.nodes.append(row_nodes)

        self.connect_without_downward_or_crossing()

        for node in self.nodes[0]:
            node.available = True

    def connect_without_downward_or_crossing(self):
        for row in range(self.rows - 1):
            current_row = self.nodes[row]
            next_row = self.nodes[row + 1]

            for node in current_row:
                # 현재 lane과 같거나 바로 옆 lane만 연결 후보로 사용한다.
                # 이렇게 하면 선이 심하게 교차하지 않고, 아래 방향 연결도 생기지 않는다.
                candidates = [
                    next_node for next_node in next_row
                    if abs(next_node.lane - node.lane) <= 1
                ]

                if len(candidates) == 0:
                    candidates = sorted(
                        next_row,
                        key=lambda next_node: abs(next_node.lane - node.lane)
                    )[:1]

                candidates = sorted(
                    candidates,
                    key=lambda next_node: abs(next_node.lane - node.lane)
                )

                node.next_nodes.append(candidates[0])

                # 가끔 하나 더 연결해서 선택지를 만든다.
                if len(candidates) > 1 and random.random() < 0.35:
                    node.next_nodes.append(candidates[1])

            # 다음 행의 모든 노드가 적어도 하나의 이전 연결을 받게 한다.
            # 접근 불가능한 방이 생기지 않도록 보정한다.
            for next_node in next_row:
                has_incoming = False

                for node in current_row:
                    if next_node in node.next_nodes:
                        has_incoming = True
                        break

                if not has_incoming:
                    nearest_prev = min(
                        current_row,
                        key=lambda node: abs(node.lane - next_node.lane)
                    )
                    nearest_prev.next_nodes.append(next_node)

            # lane 순서 기준으로 정렬해서 그림이 더 깔끔하게 보이게 한다.
            for node in current_row:
                node.next_nodes = sorted(
                    list(set(node.next_nodes)),
                    key=lambda next_node: next_node.lane
                )

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        pos = pygame.mouse.get_pos()

        for row in self.nodes:
            for node in row:
                if node.available and not node.visited and node.contains(pos):
                    self.selected_node = node
                    return node.room_type

        return None

    def complete_current_node(self):
        if self.selected_node is None:
            return

        self.selected_node.visited = True
        self.current_node = self.selected_node

        # Only rooms connected upward from the current room are selectable.
        # This prevents moving sideways or downward to previously available rooms.
        for row in self.nodes:
            for node in row:
                node.available = False

        for next_node in self.selected_node.next_nodes:
            next_node.available = True

        if self.selected_node.room_type == "BOSS":
            self.floor += 1
            self.message = "Boss cleared! New map generated."
            self.generate_map()
            self.current_node = None
            self.selected_node = None
        else:
            self.message = "Choose the next connected room"

    def draw_text(self, screen, text, x, y, font=None, color=(230, 230, 230)):
        if font is None:
            font = self.font
        img = font.render(text, True, color)
        screen.blit(img, (x, y))

    def get_node_color(self, node):
        if node.visited:
            return (80, 80, 80)

        if node.available:
            if node.room_type == "MONSTER":
                return (190, 70, 70)
            if node.room_type == "BOSS":
                return (160, 40, 170)
            if node.room_type == "TREASURE":
                return (210, 170, 60)
            if node.room_type == "REST":
                return (70, 170, 100)
            if node.room_type == "EVENT":
                return (80, 120, 200)
            return (180, 180, 180)

        return (45, 45, 55)

    def get_node_label(self, node):
        labels = {
            "START": "S",
            "MONSTER": "M",
            "TREASURE": "T",
            "EVENT": "?",
            "REST": "R",
            "BOSS": "B"
        }
        return labels.get(node.room_type, "?")

    def draw(self, screen):
        self.draw_text(screen, f"Dungeon Map - Floor {self.floor}", 345, 25, self.big_font)
        self.draw_text(screen, self.message, 350, 68, self.font, (200, 200, 220))

        self.draw_text(
            screen,
            f"Player HP {self.player_hp}/{self.player_max_hp}",
            35,
            28,
            self.font,
            (235, 235, 235)
        )

        hp_ratio = max(0, self.player_hp) / self.player_max_hp
        pygame.draw.rect(screen, (60, 60, 60), (35, 58, 210, 22))
        pygame.draw.rect(screen, (200, 40, 40), (35, 58, 210 * hp_ratio, 22))
        pygame.draw.rect(screen, (240, 240, 240), (35, 58, 210, 22), 2)

        for row in self.nodes:
            for node in row:
                for next_node in node.next_nodes:
                    # 현재 선택 가능한 루트와 이미 지난 루트만 밝게 표시
                    color = (70, 70, 90)

                    if node.visited or node.available:
                        color = (180, 180, 200)

                    pygame.draw.line(
                        screen,
                        color,
                        (node.x, node.y),
                        (next_node.x, next_node.y),
                        3
                    )

        for row in self.nodes:
            for node in row:
                color = self.get_node_color(node)

                pygame.draw.circle(screen, color, (node.x, node.y), node.radius)
                pygame.draw.circle(screen, (230, 230, 240), (node.x, node.y), node.radius, 3)

                label = self.get_node_label(node)
                label_img = self.big_font.render(label, True, (255, 255, 255))
                screen.blit(
                    label_img,
                    (
                        node.x - label_img.get_width() // 2,
                        node.y - label_img.get_height() // 2
                    )
                )

        self.draw_text(screen, "M: Monster   ?: Event   T: Treasure   R: Rest   B: Boss", 250, 665)
