
import logger
log = logger.Logger()


class CasinoPlayer:
    """ Class for a casino player """
    def __init__(self, name: str):
        self.name = name
        self.chips = 100
        self.human = True

    def place_bet(self, amount: int):
        """ place a place_bet """
        if amount <= self.chips:
            self.chips -= amount
            # log.message(f'{self.name} bet: {amount}, chips left: {self.chips}')
            return amount
        else:
            raise Exception(f"Not enough chips, bet: '{amount}', chips: '{self.chips}' for player: '{self.name}'")