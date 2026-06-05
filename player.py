import random
from card import Card


class Player:
    def __init__(self):
        self.max_hp = 80
        self.hp = 80
        self.block = 0
        self.energy = 3
        self.max_energy = 3

        self.draw_pile = [
            Card("Strike", 1, damage=5),
            Card("Strike", 1, damage=5),
            Card("Strike", 1, damage=5),
            Card("Defend", 1, block=5),
            Card("Defend", 1, block=5),
            Card("Heavy Hit", 2, damage=14),
            Card("Guard", 2, block=12),
            Card("Cheat", 0, damage=1000),
        ]

        self.hand = []
        self.discard_pile = []

        random.shuffle(self.draw_pile)

    def start_turn(self, draw_now=True):
        self.block = 0
        self.energy = self.max_energy

        if draw_now:
            self.draw_cards(5)

    def draw_cards(self, count):
        for _ in range(count):
            if len(self.draw_pile) == 0:
                if len(self.discard_pile) == 0:
                    return

                self.draw_pile = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.draw_pile)

            self.hand.append(self.draw_pile.pop())

    def discard_hand(self):
        self.discard_pile.extend(self.hand)
        self.hand = []
