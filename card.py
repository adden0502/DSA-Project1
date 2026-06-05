class Card:
    def __init__(self, name, cost, damage=0, block=0):
        self.name = name
        self.cost = cost
        self.damage = damage
        self.block = block
        self.rect = None

        self.last_actual_damage = 0
        self.last_blocked_damage = 0

    def use(self, player, enemy):
        if player.energy < self.cost:
            return False

        player.energy -= self.cost

        self.last_actual_damage = 0
        self.last_blocked_damage = 0

        if self.damage > 0:
            if hasattr(enemy, "take_damage"):
                actual_damage, blocked = enemy.take_damage(self.damage)
                self.last_actual_damage = actual_damage
                self.last_blocked_damage = blocked
            else:
                enemy.hp -= self.damage
                self.last_actual_damage = self.damage

        if self.block > 0:
            player.block += self.block

        return True
