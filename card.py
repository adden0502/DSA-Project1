class Card:
    def __init__(self, name, cost, damage=0, block=0):
        self.name = name
        self.cost = cost
        self.damage = damage
        self.block = block
        self.rect = None

    def use(self, player, enemy):
        if player.energy < self.cost:
            return False

        player.energy -= self.cost

        if self.damage > 0:
            enemy.hp -= self.damage

        if self.block > 0:
            player.block += self.block

        return True