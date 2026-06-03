class Enemy:
    def __init__(self):
        self.max_hp = 50
        self.hp = 50
        self.block = 0
        self.intent = "Attack"

    def take_turn(self, player):
        damage = 8
        actual_damage = max(0, damage - player.block)
        player.hp -= actual_damage
        player.block = max(0, player.block - damage)