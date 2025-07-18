import ast
import random
from player import CasinoPlayer

class RoulettePlayer(CasinoPlayer):
    def __init__(self, name: str):
        super().__init__(name)
        self.bet_positions = dict() # like {<bet positions>: <amount>, ...} ex: {(23): 5.0, (2,5): 12.0, (12,15,11,14): 15.0}
        self._running_winning_numbers = [] # type: list[str] # a list of winning positions after the wheel is spun
        self.running_bank = []

    def place_bet(self, positions: tuple, amount: float, wheel_positions: list):
        """ positions is a list of 1, 2, or 4 positions to bet. If more than one position is given the numbers must be
        adjacent on the table.
        :param positions: A list of positions to bet on, like [23] or [2, 5] or [12, 15, 11, 14]
        :param amount: The amount of the bet to place
        :param wheel_positions: The positions on the roulette wheel, like ['0', '1', '2', ..., '36'] for European roulette
        """

        if not isinstance(positions, list|tuple) or len(positions) not in [1, 2, 3, 4]:
            positions = [positions] # its a position like '12', make it a list

        pos_check = list((pos not in wheel_positions for pos in positions))
        if any(pos_check):
            raise ValueError(f"Invalid bet positions: '{positions}'. Positions must be in: '{wheel_positions}'.")

        if amount <= 0:
            raise ValueError("Bet amount must be greater than zero.")

        self.bet_positions.update({tuple(positions): amount})
        self.chips -= amount
        # self.running_bank.append(self.chips)

    def payout(self, money_in):
        """ use to help track the running bank account """
        if money_in > 0: # note, the chips are removed in the "place_bet method"
            self.chips += money_in
        self.running_bank.append(self.chips)

    def place_dict_bet(self, bet: dict, wheel_positions: list):
        """ places a dictionary style bet
        :bet: A dictionary like {<bet positions>: <amount>, ...} example {(23): 5.0, (2,5): 12.0, (12,15,11,14): 15.0}"""
        for positions, amount in bet.items():
            self.place_bet(positions, amount, wheel_positions)

    def update_after_spin(self, winner=False, amount=0, position='0'):
        """ Updates the player after a spin
        :winner: If True, the player won. If False, the player lost.
        :amount: The amount won or lost.
        :position: The winning position. """
        if winner:
            self._running_winning_numbers.append(position)
        self.payout(amount)

    def __str__(self):
        return f"PokerPlayer: {self.name}, Chips: {self.chips}, Bets: {self.bet_positions}, Winning Numbers: {self._running_winning_numbers}"




class RouletteTable:

    def __init__(self, european=True):
        """ Initializes the roulette table with a wheel and players
        :param european: If True, uses European roulette with a single zero. If False, uses American roulette with a double zero. """

        self._wheel_positions = [str(n) for n in range(0, 36)] # a list of strings representing the positions on the roulette wheel
        self._european_table = european # type: bool # if ture ads the '00' position for American roulette
        if european is False:
            self._wheel_positions.append('00')

        self._players = [] # type: [RoulettePlayer]
        self._winning_positions = [] # type: list[str] # a list of winning positions after the wheel is spun

        self._red_black_lut = {
            '0': 'green', '00': 'green',
            '1': 'red', '2': 'black', '3': 'red', '4': 'black', '5': 'red',
            '6': 'black', '7': 'red', '8': 'black', '9': 'red', '10': 'black',
            '11': 'red', '12': 'black', '13': 'red', '14': 'black', '15': 'red',
            '16': 'black', '17': 'red', '18': 'black',
            '19': 'red', '20': 'black', '21': 'red', '22': 'black', '23': 'red',
            '24': 'black', '25': 'red', '26': 'black', '27': 'red', '28': 'black',
            '29': 'red', '30': 'black', '31': 'red', '32': 'black', '33': 'red',
            '34': 'black', '35': 'red', '36': 'black'}

    def add_player(self, player: RoulettePlayer):
        """ Adds a player to the roulette table
        :param player: The player to add. """
        if not isinstance(player, RoulettePlayer):
            raise ValueError("Player must be an instance of RoulettePlayer")
        self._players.append(player)

    def spin_the_wheel(self):
        """ Simulates spinning the roulette wheel and pays out the winners """

        debug = False # todo: don't commit if this is True
        if debug is False:
            winning_position = random.choice(self._wheel_positions) # type: str # like '23' or '00'
        else:
            winning_position = '3'

        self._winning_positions.append(winning_position)
        for player in self._players: # type: RoulettePlayer

            payout = 0
            winner = False
            # iterate over positions and look for a winner
            for positions, amount in player.bet_positions.items(): # positions like: (23) or (2,5); amount like 10.0

                str_pos = list((str(p) for p in positions)) # the string version of the positions, like ('23') or ('2', '5')

                if winning_position in str_pos: # check if the player has a bet on the winning position
                    winner = True

                    if len(positions) == 1:
                        payout = amount * 36

                    elif len(positions) == 2:
                        payout = amount * 17

                    elif len(positions) == 3:
                        payout = amount * 11

                    elif len(positions) == 4:
                        payout = amount * 8

            player.update_after_spin(winner, payout, winning_position)
        return winning_position

    def get_table_numbers_string(self) -> str:
        if self._european_table is True:
            table = """
                    +------------------------------------------------------------+
                        | 3 | 6 | 9 | 12 | 15 | 18 | 21 | 24 | 27 | 30 | 33 | 36 |
                         --------------------------------------------------------
                      0 | 2 | 5 | 8 | 11 | 14 | 17 | 20 | 23 | 26 | 29 | 32 | 35 |
                         --------------------------------------------------------
                        | 1 | 4 | 7 | 10 | 13 | 16 | 19 | 22 | 25 | 28 | 31 | 34 |
                    +------------------------------------------------------------+
                    """
        else:
            table = """
                    +------------------------------------------------------------+
                      0 | 3 | 6 | 9 | 12 | 15 | 18 | 21 | 24 | 27 | 30 | 33 | 36 |
                         --------------------------------------------------------
                    ----| 2 | 5 | 8 | 11 | 14 | 17 | 20 | 23 | 26 | 29 | 32 | 35 |
                         --------------------------------------------------------
                     00 | 1 | 4 | 7 | 10 | 13 | 16 | 19 | 22 | 25 | 28 | 31 | 34 |
                    +------------------------------------------------------------+
                """
        # creates a string like below that shows the winning positions and their color:
        """
        Red   : 3    7  22 
        Black :   4         29
        """
        red_str =   "Red   : "
        black_str = "Black : "
        grn_str =   "Green : "

        wins_to_show  = self._winning_positions[-25:] if len(self._winning_positions) >= 25 else self._winning_positions
        for pos in wins_to_show: # only show the last 25 winning positions
                color = self._red_black_lut[pos]
                if color == 'red':
                    red_str += f" {pos:2} "
                    black_str += f"    "
                    grn_str += f"    "
                elif color == 'black':
                    red_str += f"    "
                    black_str += f" {pos:2} "
                    grn_str += f"    "
                else: # green
                    red_str += f"    "
                    black_str += f"    "
                    grn_str += f" {pos:2} "

        player = "Hit the Run Simulation button"
        if len(self._players) > 0:
            player = f"{self._players[0]}"

        state_string = f"{table}\n\n\nWinning Numbers:\n{red_str}\n{black_str}\n{grn_str}\n\nPlayer: {player}"

        return state_string

    def get_game_state_string(self) -> str:
        return self.get_table_numbers_string()

    def table_place_bet(self, positions: str, amounts: str, player_name='Bob'):
        """ parses positions like "1, (2,3), 16" and bets like "5, 10, 15" and places the bets for the player"""

        amt_tup = ast.literal_eval(amounts)
        positions_list = positions.split(',') # convert the string to an intermediate list like: # ['1', '(2', '3)', '16']

        # loop over the list and pull out tuples
        _open = False
        _inner = []
        updated_positions = []
        for st in positions_list: # need to clean up user input to something useful

            if '(' in st:
                _open = True
                _inner.append(st.replace('(', ''))
                continue # --------------------------------------------------------------------------------------------^

            if _open is True:
                if ')' in st:
                    _inner.append(st.replace(')', ''))
                    updated_positions.append(tuple(_inner))
                    _inner = []
                    _open = False
                else:
                    _inner.append(st)
                continue # --------------------------------------------------------------------------------------------^

            else:
                updated_positions.append(st)

        # all the bet positions need to be iterables, so convert them if they are strings
        formatted_positions = [(p,) if isinstance(p, str) else p for p in updated_positions]

        # multiple value betting, need to check a few things
        if isinstance(amt_tup, tuple):
            len_bets = len(amt_tup)
            len_positions = len(positions_list)

            if len_bets != len_positions:
                raise ValueError(f"Number of bets {len_bets} does not match number of positions {len_positions}") # !

            # iterate over positions(p) and amounts(a) and place the bets
            bets = {p:a for p, a in zip(formatted_positions, amt_tup)}

        else: # a single amount for all positions
            try:
                bets = {p:amt_tup for p in formatted_positions}
            except Exception as ex:
                raise ValueError(f"Error parsing bets: {ex}")

        for player in self._players:
            if player.name == player_name:
                player.place_dict_bet(bets, self._wheel_positions)
            else:
                raise ValueError(f"Player {player_name} not found")








