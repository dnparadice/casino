""" a module that implements the necessary objects and methods to deal and score a
digital poker game """

import os
import multiprocessing as mp
import time
from enum import Enum
import random
from copy import copy, deepcopy
from multiprocessing.spawn import freeze_support
import itertools

from fontTools.ttLib.tables.C_F_F_ import table_C_F_F_

from player import CasinoPlayer

from logger import Logger
log = Logger()


class Suit(Enum):
    """ Enum class for the suit of a card """
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    SPADES = 4

    def get_printable_suit(self):
        """ return the printable suit of a card """
        if self.name == 'HEARTS':
            return '♥'
        elif self.name == 'DIAMONDS':
            return '♦'
        elif self.name == 'CLUBS':
            return '♣'
        elif self.name == 'SPADES':
            return '♠'


class CardRank(Enum):
    """ Enum class for the rank of a card """
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def get_printable_rank(self):
        """ return the printable rank of a card """
        if self.value < 11:
            return str(self.value)
        else:
            return self.name[0]


class HandRank(Enum):
    """ Enum class for the rank of a hand """
    INITIAL = 0
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9

    def __gt__(self, other):
        """ compare two hand ranks, used for sorting """
        if self.value > other.value:
            return True
        return False


class PokerGames(Enum):
    """ Enum class for the type of poker game """
    TEXAS_HOLD_EM = 1
    OMAHA = 2
    SEVEN_CARD_STUD = 3
    FIVE_CARD_DRAW = 4


class GameState(Enum):
    """ Enum class for the state of the game """
    PRE_DEAL = 0
    INITIAL_DEAL = 10
    PRE_FLOP_BET = 20
    POST_FLOP_BET = 40
    POST_TURN_BET = 60
    POST_RIVER_BET = 80
    SHOWDOWN = 90
    END_GAME = 100


class HandProbability:
    """ Probabilities for a 5 card hand, default is the known 5 card hand probabilities """
    def __init__(self):
        self.straight_flush =  0.0000139   # ((10c1)(4c1)-(4c1))/(52c5),          odds: 72,192.33
        self.four_of_a_kind =  0.0002401   # (13c1)(4c4)(12c1)(4c1)/(52c5),       odds: 4,165.33
        self.full_house =      0.00144058  # (13c1)(4c3)(12c1)(4c2)/(52c5),       odds: 693.17
        self.flush =           0.0019654   # ((13c5)(4c1)-(10c1)(4c1))/(52c5),    odds: 508.8
        self.straight =        0.00392465  # ((10c1)*(4c1)^5-(10c1)(4c1))/(50c5), odds: 253.8
        self.three_of_a_kind = 0.02112845  # (13c1)(4c3)(12c2)(4c1)^2/(52c5),     odds: 46.3
        self.two_pair =        0.04753902  # (13c2)(4c2)^2*(11c1)(4c1)/(52c5),    odds: 20.0
        self.pair =            0.42256903  # (13c1)(4c2)(12c3)(4c1)^3/(52c5),     odds: 1.36

    def __sub__(self, other):
        self.straight_flush -=  other.straight_flush
        self.four_of_a_kind -=  other.four_of_a_kind
        self.full_house -=      other.full_house
        self.flush -=           other.flush
        self.straight -=        other.straight
        self.three_of_a_kind -= other.three_of_a_kind
        self.two_pair -=        other.two_pair
        self.pair -=            other.pair
        return self

    def _set_all_to_zero(self):
        """ set all probabilities to zero """
        self.straight_flush = 0
        self.four_of_a_kind = 0
        self.full_house = 0
        self.flush = 0
        self.straight = 0
        self.three_of_a_kind = 0
        self.two_pair = 0
        self.pair = 0

    def get_delta_probability(self, filter = None):
        """ get the delta probability for a hand rank, note that this can be a + or - delta
        @param: filter: a list of HandRank objects to include, default is None (include all HandRanks)
        @return: HandProbability object with the delta probabilities for the hand ranks in the filter """
        base_prob = HandProbability()
        delta_prob = HandProbability()
        delta_prob._set_all_to_zero()
        if filter is None:
            filter = [HandRank.STRAIGHT_FLUSH, HandRank.FOUR_OF_A_KIND, HandRank.FULL_HOUSE,
                      HandRank.FLUSH, HandRank.STRAIGHT, HandRank.THREE_OF_A_KIND,
                      HandRank.TWO_PAIR, HandRank.PAIR]

        for hand_rank in filter: # type: HandRank
            base_prob_value =  base_prob.get_probability_for_rank(hand_rank)
            self_prob_value = self.get_probability_for_rank(hand_rank)

            # calculate the delta
            delta = self_prob_value - base_prob_value

            if hand_rank == HandRank.STRAIGHT_FLUSH:
                delta_prob.straight_flush = delta
            elif hand_rank == HandRank.FOUR_OF_A_KIND:
                delta_prob.four_of_a_kind = delta
            elif hand_rank == HandRank.FULL_HOUSE:
                delta_prob.full_house = delta
            elif hand_rank == HandRank.FLUSH:
                delta_prob.flush = delta
            elif hand_rank == HandRank.STRAIGHT:
                delta_prob.straight = delta
            elif hand_rank == HandRank.THREE_OF_A_KIND:
                delta_prob.three_of_a_kind = delta
            elif hand_rank == HandRank.TWO_PAIR:
                delta_prob.two_pair = delta
            elif hand_rank == HandRank.PAIR:
                delta_prob.pair = delta

        return delta_prob

    def get_delta_probability_sum(self, weights=None, ignore_negatives=True):
        """ get the delta probability sum for a hand rank, this is a figure of merit that aids in determining
        the strength of a hand.

        @param: weights[dictionary]: a dict of weights for each hand rank, the weight value between 0 and 1
                                    default (if None is passed):
                                    {HandRank.STRAIGHT_FLUSH: 1,
                                    HandRank.FOUR_OF_A_KIND: 0.9,
                                    HandRank.FULL_HOUSE: 0.8,
                                    HandRank.FLUSH: 0.7,
                                    HandRank.STRAIGHT: 0.6,
                                    HandRank.THREE_OF_A_KIND: 0.5,
                                    HandRank.TWO_PAIR: 0.4,
                                    HandRank.PAIR: 0.3}
        @param: ignore_negatives: if True, only sum the positive changes in probability, default is True
        @return: sum of the delta probabilities for the hand ranks in the filter """

        # in the case that you have two cards of different suite you can not get a flush, so the probability
        # of the flush goes to Zero resulting in a negative delta, this it typically not useful to sum these

        hr = HandRank
        if weights is None:
            weights = {hr.STRAIGHT_FLUSH: 1,
                        hr.FOUR_OF_A_KIND: 0.9,
                        hr.FULL_HOUSE: 0.8,
                        hr.FLUSH: 0.7,
                        hr.STRAIGHT: 0.6,
                        hr.THREE_OF_A_KIND: 0.5,
                        hr.TWO_PAIR: 0.4,
                        hr.PAIR: 0.3,}
        delta_prob = self.get_delta_probability()

        # iterate over delta_prob and set to 0 if ignore_negatives is True and the value is negative
        if ignore_negatives is True:
            zd = copy(delta_prob)
            for key, value in vars(delta_prob).items():
                if value < 0:
                    zd.__setattr__(key, 0)
                else:
                    zd.__setattr__(key, value)
            delta_prob = zd

        # iterate over the delta probabilities and multiply by the weights
        rsum = 0  # running sum
        if delta_prob.straight_flush != 0:
            rsum += delta_prob.straight_flush * weights.get(hr.STRAIGHT_FLUSH, 1)
        elif delta_prob.four_of_a_kind != 0:
            rsum += delta_prob.four_of_a_kind * weights.get(hr.FOUR_OF_A_KIND, 0.9)
        elif delta_prob.full_house != 0:
            rsum += delta_prob.full_house * weights.get(hr.FULL_HOUSE, 0.8)
        elif delta_prob.flush != 0:
            rsum += delta_prob.flush * weights.get(hr.FLUSH, 0.7)
        elif delta_prob.straight != 0:
            rsum += delta_prob.straight * weights.get(hr.STRAIGHT, 0.6)
        elif delta_prob.three_of_a_kind != 0:
            rsum += delta_prob.three_of_a_kind * weights.get(hr.THREE_OF_A_KIND, 0.5)
        elif delta_prob.two_pair != 0:
            rsum += delta_prob.two_pair * weights.get(hr.TWO_PAIR, 0.4)
        elif delta_prob.pair != 0:
            rsum += delta_prob.pair * weights.get(hr.PAIR, 0.3)
        return rsum


    def get_probability_for_rank(self, hand_rank: HandRank):
        """ get the probability of a hand rank
        Warning, when a game is active these probabilities may be updated from default depending on the existing hand """
        if hand_rank == HandRank.STRAIGHT_FLUSH:
            return self.straight_flush
        elif hand_rank == HandRank.FOUR_OF_A_KIND:
            return self.four_of_a_kind
        elif hand_rank == HandRank.FULL_HOUSE:
            return self.full_house
        elif hand_rank == HandRank.FLUSH:
            return self.flush
        elif hand_rank == HandRank.STRAIGHT:
            return self.straight
        elif hand_rank == HandRank.THREE_OF_A_KIND:
            return self.three_of_a_kind
        elif hand_rank == HandRank.TWO_PAIR:
            return self.two_pair
        elif hand_rank == HandRank.PAIR:
            return self.pair
        else:
            raise Exception('Invalid hand rank')


class Card:
    """ Class for a card object """
    def __init__(self, rank: CardRank, suit: Suit):
        if isinstance(rank, int):
            rank = CardRank(rank)
        self.rank = rank
        self.suit = suit

    def __str__(self):
        ps = self.suit.get_printable_suit()
        return f'({ps} {self.rank.name} {ps})'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.rank == other.rank and self.suit == other.suit:
            return True
        return False

    def __gt__(self, other):
        return self.rank.value > other.rank.value

    def __sub__(self, other):
        return self.rank.value - other.rank.value


class Deck:
    """ Class for a deck object """
    def __init__(self):
        self.cards = [] # cards are popped when dealt, this represents the deck in play
        self.build()    # adds the cards to the deck
        self._all_cards = copy(self.cards) # used to store cards for resetting the deck / game

    def build(self):
        """ create a deck of 52 cards """
        for suit in Suit:
            for rank in CardRank:
                self.cards.append(Card(rank, suit))

    def shuffle(self):
        """ shuffle the deck """
        random.shuffle(self.cards)

    def deal(self, num_cards):
        """ deal n cards from the deck """
        return [self.cards.pop() for _ in range(num_cards)]

    def reset_deck(self):
        """ reset the deck to the original state """
        self.cards = copy(self._all_cards)

    def __str__(self):
        deck_str = ''
        for card in self.cards:
            deck_str += f'{card}\n'
        return deck_str


class PartialDeck(Deck):
    """ Class for a partial deck object, used in probability calculations """
    def __init__(self, throw_out_cards=[]):
        """ pass a list of cards to throw out to the constructor. This deck will never contain those cards """
        super().__init__()
        for card in throw_out_cards:
            self.cards.remove(card)
            self._all_cards.remove(card)


class Hand:
    """ Class for a hand object """
    def __init__(self):
        self.cards = []
        self.hand_rank = HandRank.INITIAL
        self.straight_cards = []  # type: list[Card]
        self.winning_cards = []  # type: list[Card]

        # the high card for the 5 card poker hand ie: not always the highest card
        self.significant_high_card = None  # type: Card | None

    def __add__(self, other):
        """ add two hands together """
        return self.add_cards(other.cards)

    def add_cards(self, cards: list):
        """ add a card to the hand """
        self.cards.extend(cards)

    def __str__(self):
        hand_str = ''
        for card in self.cards:
            hand_str += f'{card} '
        return hand_str

    def __repr__(self):
        l = str([c for c in self.cards])
        r = str(self.hand_rank)
        return "Hand" + r + l

    def print_hand(self, cards=None):
        """ print the hand,
        @ cards: a list of cards to print instead of the hand if None
                        the existing hand will be printed"""
        if cards is None:
            cards = self.cards
        for card in cards:
            print('+--------+ ', end='')
        print()
        for card in cards:
            rnk = card.rank.get_printable_rank()
            if rnk != '10':
                print(f'|{rnk}       | ', end='')
            else:
                print(f'|{rnk}      | ', end='')
        print()
        for card in cards:
            print('|        | ', end='')
        print()
        for card in cards:
            print(f'|    {card.suit.get_printable_suit()}   | ', end='')
        print()
        for card in cards:
            print('|        | ', end='')
        print()
        for card in cards:
            rnk = card.rank.get_printable_rank()
            if rnk != '10':
                print(f'|       {rnk}| ', end='')
            else:
                print(f'|      {rnk}| ', end='')
        print()
        for card in cards:
            print('+--------+ ', end='')
        print()

    def get_string_hand(self, cards=None):
        """ same as print_hand but returns a string """
        if cards is None:
            cards = self.cards
        hand_str = ''
        for card in cards:
            hand_str += '+--------+ '
        hand_str += '\n'
        for card in cards:
            rnk = card.rank.get_printable_rank()
            if rnk != '10':
                hand_str += f'|{rnk}       | '
            else:
                hand_str += f'|{rnk}      | '
        hand_str += '\n'
        for card in cards:
            hand_str += '|        | '
        hand_str += '\n'
        for card in cards:
            hand_str += f'|    {card.suit.get_printable_suit()}   | '
        hand_str += '\n'
        for card in cards:
            hand_str += '|        | '
        hand_str += '\n'
        for card in cards:
            rnk = card.rank.get_printable_rank()
            if rnk != '10':
                hand_str += f'|       {rnk}| '
            else:
                hand_str += f'|      {rnk}| '
        hand_str += '\n'
        for card in cards:
            hand_str += '+--------+ '
        hand_str += '\n'
        return hand_str

    def score_5_or_7_card_hand(self, print_cards_and_rank=False) -> list:
        """ score the hand of 5 cards
        @param: print_cards_and_rank: if True, print the cards and the rank of the hand
        @return: list of ranks achieved by the hand, includes all achieved like [HandRank.PAIR, HandRank.FLUSH, HandRank.THREE_OF_A_KIND]
        """
        self.hand_rank = HandRank.INITIAL
        ranks = [] # a list of all ranks achieved in hand

        # make copy and sort the cards
        tmp = copy(self.cards)
        tmp.sort(key=lambda x: x.rank.value)
        # self.print_hand(tmp)

        # check for high card
        self.hand_rank = HandRank.HIGH_CARD
        ranks.append(HandRank.HIGH_CARD)
        self.significant_high_card = tmp[-1]
        self.winning_cards.append(self.significant_high_card)

        # check for pairs
        pair_count = 0
        for i in range(len(tmp) - 1):
            if tmp[i].rank == tmp[i+1].rank:
                if pair_count == 0:
                    self.significant_high_card = tmp[i]
                    pair_count = 1
                    self.winning_cards = [tmp[i], tmp[i+1]]
                if pair_count == 1:
                    if tmp[i+1].rank == self.significant_high_card.rank:
                        continue # this is either a 3 or 4 of a kind, don't count it as 2 pair
                    else:
                        pair_count = 2
                        self.winning_cards += [tmp[i], tmp[i+1]]


        if pair_count == 1:
            self.hand_rank = HandRank.PAIR
            ranks.append(HandRank.PAIR)
        elif pair_count == 2:
            self.hand_rank = HandRank.TWO_PAIR
            ranks.append(HandRank.PAIR)
            ranks.append(HandRank.TWO_PAIR)

        # check for three of a kind
        three_of_a_kind = [] # this is used later for full house check
        for i in range(len(tmp) - 2): # convolve the pattern and the list
            if tmp[i].rank == tmp[i + 1].rank == tmp[i + 2].rank:
                self.hand_rank = HandRank.THREE_OF_A_KIND
                ranks.append(HandRank.THREE_OF_A_KIND)
                self.significant_high_card = tmp[i+2]
                three_of_a_kind.append(tmp[i])
                three_of_a_kind.append(tmp[i+1])
                three_of_a_kind.append(tmp[i+2])
                self.winning_cards = three_of_a_kind
                break

        # check for straight
        straight = False
        # check for duplicates, creates a list of unique rank cards
        unique_rank_values = []
        unique_rank_cards = []
        for card in tmp:
            if card.rank.value not in unique_rank_values:
                unique_rank_values.append(card.rank.value)
                unique_rank_cards.append(card)

        # check distance between each unique rank card
        distances = []
        for i in range(len(unique_rank_cards) - 1):
            distances.append(unique_rank_cards[i+1].rank.value - unique_rank_cards[i].rank.value)
        # print(f"distances: {distances}")
        pattern = [1, 1, 1, 1]
        rng = range(len(unique_rank_cards) - 4)
        for i in rng:
            slice = distances[i:i+4]
            # print(f"Slice {i}: {slice}")
            if slice == pattern:
                self.hand_rank = HandRank.STRAIGHT
                ranks.append(HandRank.STRAIGHT)
                straight = True
                self.straight_cards = unique_rank_cards[i:i+5]
                self.winning_cards = self.straight_cards
                break

        # check for flush
        flush = False
        for suit in Suit:
            check = [card for card in tmp if card.suit == suit]
            if len(check) >= 5:
                self.hand_rank = HandRank.FLUSH
                ranks.append(HandRank.FLUSH)
                flush = True
                self.winning_cards = check
                break

        # check for full house
        if self.hand_rank == HandRank.THREE_OF_A_KIND:
            lcl = copy(tmp)
            for card in tmp:
                if card.rank.value == self.significant_high_card.rank.value:
                    lcl.remove(card) # this removes all the three of a kind cards

            for i in range(len(lcl) - 1):
                if lcl[i].rank == lcl[i+1].rank:
                    self.hand_rank = HandRank.FULL_HOUSE
                    ranks.append(HandRank.FULL_HOUSE)
                    three_of_a_kind.append(lcl[i])
                    three_of_a_kind.append(lcl[i+1])
                    self.winning_cards = three_of_a_kind

        # check for four of a kind
        for i in range(len(tmp) - 3):
            if tmp[i].rank == tmp[i+1].rank == tmp[i+2].rank == tmp[i+3].rank:
                self.hand_rank = HandRank.FOUR_OF_A_KIND
                ranks.append(HandRank.FOUR_OF_A_KIND)
                self.significant_high_card = tmp[i]
                self.winning_cards = [tmp[i], tmp[i+1], tmp[i+2], tmp[i+3]]

        # check for straight flush
        if straight and flush:
            for card in self.straight_cards:
                if card.suit.value != self.straight_cards[0].suit.value:
                    break
            else:
                self.hand_rank = HandRank.STRAIGHT_FLUSH
                ranks.append(HandRank.STRAIGHT_FLUSH)
                self.winning_cards = self.straight_cards

        if print_cards_and_rank is True:
            self.print_hand(self.winning_cards)
            # finally print the rank
            print(f"Hand Rank: [{self.hand_rank.name}], significant high card: {self.significant_high_card}")

        return ranks

    def score_partial_hand(self, cards=None):
        """ score up to 4 cards """
        if cards is None:
            cards = self.cards

        self.hand_rank = HandRank.INITIAL

        # make copy and sort the cards
        tmp = copy(cards)
        tmp.sort(key=lambda x: x.rank.value)
        # self.print_hand(tmp)

        # check for high card
        self.hand_rank = HandRank.HIGH_CARD
        self.significant_high_card = tmp[-1]
        self.winning_cards.append(self.significant_high_card)

        # check for pairs
        pair_count = 0
        for i in range(len(tmp)-1):
            if tmp[i].rank == tmp[i+1].rank:
                self.hand_rank = HandRank.PAIR
                self.significant_high_card = tmp[i]
                pair_count += 1
                self.winning_cards = [tmp[i], tmp[i+1]]

        if pair_count == 1:
            self.hand_rank = HandRank.PAIR
        elif pair_count == 2:
            self.hand_rank = HandRank.TWO_PAIR

        # check for three of a kind
        for i in range(len(tmp)-2):
            if tmp[i].rank == tmp[i+1].rank == tmp[i+2].rank:
                self.hand_rank = HandRank.THREE_OF_A_KIND
                self.significant_high_card = tmp[i]
                self.winning_cards = [tmp[i], tmp[i+1], tmp[i+2]]

        # check for straight
        straight = False
        # check for duplicates
        unique_rank = []
        unique_cards = []
        for card in tmp:
            if card.rank.value not in unique_rank:
                unique_rank.append(card.rank.value)
                unique_cards.append(card)
        if len(unique_rank) != len(tmp):
            # self.print_hand(unique_cards)
            tmp = unique_cards

        # check distance between each card
        distances = []
        for i in range(len(tmp) - 1):
            distances.append(tmp[i+1].rank.value - tmp[i].rank.value)
        # print(f"distances: {distances}")
        pattern = [1, 1, 1]
        rng = range(len(tmp) - 3)
        for i in rng:
            slice = distances[i:i+3]
            # print(f"Slice {i}: {slice}")
            if slice == pattern:
                self.hand_rank = HandRank.STRAIGHT
                straight = True

                self.straight_cards = tmp[i:i+4]
                self.winning_cards = self.straight_cards
                break

        # check for flush
        flush = False
        for suit in Suit:
            check = [card for card in tmp if card.suit == suit]
            if len(check) >= 4:
                self.hand_rank = HandRank.FLUSH
                flush = True
                self.winning_cards = check
                break

        # check for full house - cant have full house with 4 cards

        # check for four of a kind
        for i in range(len(tmp)-1):
            if tmp[i].rank == tmp[i+1].rank == tmp[i+2].rank == tmp[i+3].rank:
                self.hand_rank = HandRank.FOUR_OF_A_KIND
                self.significant_high_card = tmp[i]
                self.winning_cards = [tmp[i], tmp[i+1], tmp[i+2], tmp[i+3]]

        # check for straight flush
        if straight and flush:
            for card in self.straight_cards:
                if card.suit.value != self.straight_cards[0].suit.value:
                    break
            else:
                self.hand_rank = HandRank.STRAIGHT_FLUSH
                self.winning_cards = self.straight_cards

        self.print_hand(self.winning_cards)
        # finally print the rank
        print(f"Hand Rank: [{self.hand_rank.name}], significant high card: {self.significant_high_card}")
        return self.hand_rank, self.significant_high_card

    def reset_hand(self):
        """ like calling init but theoretically slightly faster, clears the hand and all other attributes """
        self.cards = []
        self.hand_rank = HandRank.INITIAL
        self.straight_cards = []
        self.winning_cards = []
        self.significant_high_card = None


class PokerPlayer(CasinoPlayer):
    """ Class for a poker player """
    def __init__(self, name: str):
        super().__init__(name)
        self.cards_in_hand = Hand()
        self.current_bet = 0
        self.folded = False
        self.probability_sum = 0
        self.original_bet = 0
        self.all_in = False

    def __repr__(self):
        return f'{self.name}, {self.chips} chips, {self.cards_in_hand}, current bet: {self.current_bet}, folded: {self.folded}'

    def determine_bet(self, table_cards: Hand, current_table_bet: float, bet_position: int, opponents: list,
                      game_state: GameState, bet_round_number: int):
        """ make a bet, returns the bet amount, sets the local player state. Typcially this is used for
         the AI players to determine their bet based on the current game state and their hand. Its included
         in this context so that the Humans can see what the AI would bet.
        @param: table_cards: the cards on the table, this is a Hand object
        @param: current_table_bet: the current bet of the player, this is used to determine if the player is checking or raising
        @param: bet_position: the position of the player in the betting round, this is used to determine if the player is checking or raising
        @param: opponents: a list of opponent players, this is used to determine the strength of the hand
        @param: game_state: the current state of the game, this is used to determine the betting strategy
        @param: bet_round_number: the current betting round number, this is used to determine the betting strategy index 0
        @return: the bet amount, if the player folds then the bet is 0
        """
        if self.folded is False:

            # log.message(f"{self.name} is betting ----------------------------------------------------------")

            cards_in_hand = self.cards_in_hand.cards
            table_cards = table_cards.cards
            want_to_raise = False
            want_to_fold = False

            if game_state == GameState.PRE_FLOP_BET:
                multiplier = 100
            elif game_state == GameState.POST_FLOP_BET:
                multiplier = 1
            elif game_state == GameState.POST_TURN_BET:
                multiplier = 0.5
            elif game_state == GameState.POST_RIVER_BET:
                multiplier = 0.2
            elif game_state == GameState.SHOWDOWN:
                multiplier = 0.1

            if bet_round_number == 0:

                # you may have 4 cards in your hand but you can only play 2 so you need to get the probability for all
                # combinations of 2 cards in your hand
                self.probability_sum = self._get_probability_sum(cards_in_hand, table_cards)
                self.original_bet = bet = self._get_bet_based_on_probability_sum(self.probability_sum, current_table_bet, multiplier)

                if self.current_bet != 0.0: # this is the case for the blinds
                    if self.current_bet > bet: # not sure how this happens but protect from it
                        bet = 0
                    else:
                        bet = bet - self.current_bet

            elif bet_round_number != 0: # second, third, ---> nth round of betting

                if self.current_bet >= current_table_bet:
                    r = [True] + [False] * bet_round_number # decrease the chance of raising as the bet round number increases
                    want_to_raise = random.choice(r[:bet_round_number+1]) # probability to raise goes down as bet round number increases

                    if self.probability_sum > 1 and want_to_raise is True:
                        bet = self.current_bet +1
                    else:
                        bet = 0 # bet already == to current_table_bet, so we are checking
                else:
                    fold = [False, False] + [True] * bet_round_number # increase the chance of folding as the bet round number increases
                    want_to_fold = random.choice(fold[:bet_round_number+1])  # randomly decide if we want to fold or not

                    # second round of betting, might want to be more clever here but for now
                    if want_to_fold is False: # need to match bet
                        # need to determine if to raise here
                        bet = current_table_bet - self.current_bet
                    else:
                        log.message(f'{self.name} folds')
                        self.folded = True
                        bet = 0

            if bet > self.chips: # go all in?
                bet = self.chips

        else:
            bet = 0

        log.message(
            f'BET:: {self.name} prob sum: {self.probability_sum}, new bet: {bet}, current bet : {self.current_bet}, '
            f'current table bet: {current_table_bet}, round: {bet_round_number}, raise: {want_to_raise}, '
            f'fold: {want_to_fold}, '
            f' multiplier: {multiplier}, {game_state.name}, hand: {cards_in_hand},')

        self.place_bet(bet)
        return bet

    def _get_probability_sum(self, hand_cards: list, table_cards: list):
        cnt_table_cards = len(table_cards)
        hand_combo = list(itertools.combinations(hand_cards, 2))
        if cnt_table_cards == 0:
            combination = hand_combo
        elif 1 <= cnt_table_cards <= 2:
            combination = [list(pair) + table_cards for pair in hand_combo]
        else: # table cards are 4 or 5, so we need to combine the hand with the table cards
            table_combos = list(itertools.combinations(table_cards, 2))
            c1 = []
            for combo in table_combos:
                lc = list(combo)
                c1.extend([list(pair) + lc for pair in hand_combo])
            combination = c1

        loop_prob = 0  # accumulate the probability for each loop
        for combo in combination:
            prob = self.get_n_card_probability(combo)
            filter = [HandRank.STRAIGHT_FLUSH, HandRank.FOUR_OF_A_KIND, HandRank.FULL_HOUSE,
                      HandRank.FLUSH, HandRank.STRAIGHT, HandRank.THREE_OF_A_KIND,
                      HandRank.TWO_PAIR]
            del_prob = prob.get_delta_probability()
            prob_sum = prob.get_delta_probability_sum()  # this sums the change, if > 0 its worth betting
            loop_prob += prob_sum
            # log.message(f'Check combo: {combo}, prob sum: {prob_sum}')
        return loop_prob

    def _get_bet_based_on_probability_sum(self, prob_sum: float, current_bet: float, multiplier=100):
        """ get the bet, check or fold based on the probability sum, this is a figure of merit that aids in determining
        the strength of a hand.
        @param: prob_sum: the probability sum of the hand, if > 0 then its worth betting
        @param: current_table_bet: the current bet of the player, this is used to determine if the player is checking or raising
        @param: multiplier: the multiplier to use for the bet, default is 100
        @return: the bet amount, if the player folds then the bet is 0 """
        bet = 0
        if prob_sum == 0:
            if self.current_bet == current_bet:
                # check
                bet = 0
                log.message(f'{self.name} checks')
            else:
                # fold
                self.folded = True
                bet = 0
                log.message(f'{self.name} folds')

        if prob_sum > 0.0:
            if self.current_bet == current_bet:
                # match
                bet = current_bet - self.current_bet
                self.current_bet = current_bet
                self.chips -= bet
            else:  # raise
                rs = int(prob_sum * multiplier)
                if rs < 1:
                    rs = 1
                bet = current_bet + rs
                # log.message(f'{self.name} raises {rs} chips')
        return bet

    def place_bet(self, amount: int):
        """ place a bet """
        super().place_bet(amount)
        self.current_bet += amount
        return self.current_bet

    def get_n_card_probability(self, cards: list):
        """ returns the probability for a 2, 3, or 4 card hand"""
        if len(cards) == 2:
            return self.two_card_probability(*cards)
        if len(cards) == 3:
            return self.three_card_probability(*cards)
        if len(cards) == 4:
            return self.four_card_probability(*cards)
        raise Exception(f'Invalid number of cards, {cards}')

    def two_card_probability(self, pocket_a: Card, pocket_b: Card) -> HandProbability:
        """ calculate the probability of the hand with 2 cards delt of a 52 card deck
        @ pocket_a:[Card] the first card in the hand
        @ pocket_b:[Card] the second card in the hand
         """
        hp = HandProbability()
        if pocket_a.rank.value == pocket_b.rank.value: # if you have a pair, there is some chance you will get other nice hands
            hp.pair            = 1
            hp.two_pair        = 0.269   # brute force calculated 1M hands
            hp.three_of_a_kind = 0.119   # brute force calculated 1M hands
            hp.full_house      = 0.00995 # 1M hands
            hp.four_of_a_kind  = 0.0024  # 10M hands
            hp.straight        = 0.0     # you can't have a pair and a straight
            hp.straight_flush  = 0.0

        if pocket_a.suit == pocket_b.suit:
            hp.flush = 0.0084 # Brute force calculated 1M hands

        if abs(pocket_a.rank.value - pocket_b.rank.value) == 1:
            hp.straight = 0.01312 # 1M hands
            hp.straight_flush = 0.0  # since you have two suites that are not equal
            if pocket_a.suit == pocket_b.suit:
                hp.straight_flush =  0.000197

        return hp

    def three_card_probability(self, card_a: Card, card_b: Card, card_c):
        """ calculate the probability of the hand with 3 cards delt of a 52 card deck
        @ card_a:[Card] the first card in the hand
        @ card_b:[Card] the second card in the hand
        @ card_c:[Card] the third card in the hand
        """
        hp = HandProbability()
        # check for pairs
        card_value_set = set([card_a.rank.value, card_b.rank.value, card_c.rank.value])
        if len(card_value_set) == 1:  # all cards are the same value
            hp.pair = 1
            hp.two_pair = 0.061 # Brute force calculated 1M Hands
            hp.three_of_a_kind = 1
            hp.four_of_a_kind = 0.0406  # Brute Force 3M, close to: (12c1)*(4c2)/(49c2)
            hp.full_house = 0.061  # something is fishy here, why is this the same as two pair?
            hp.straight = 0 # cant have a straight if you have a pair
            hp.straight_flush = 0 # cant have a straight flush if you have a pair

        flush = False
        card_suite_set = set([card_a.suit.value, card_b.suit.value, card_c.suit.value])
        if len(card_suite_set) == 1:
            hp.flush = 0.037889 # Brute force calculated 3M hands
            flush = True

        # check for straights
        tmp = copy([card_a, card_b, card_c])
        tmp.sort(key=lambda x: x.rank.value)
        if abs(tmp[0] - tmp[1]) == 1 and abs(tmp[1] - tmp[2]) == 1:
            # for straights the probability is higher if the cards are in the middle of the values because
            # there are more cards that can be used to make the straight, if you have 2,3,4 the only cards
            # that can complete the straight are 5,6 but if you have 7,8,9 you can use 5,6,10,11 to complete
            # the straight.
            vals = [card_a.rank.value, card_b.rank.value, card_c.rank.value]
            if 2 in vals or 14 in vals:
                hp.straight = 0.013
                if flush is True:
                    hp.straight_flush = 0.0008
            elif 3 in vals or 13 in vals:
                hp.straight = 0.027
                if flush is True:
                    hp.straight_flush = 0.0016
            else: # cards are in the middle of the value range
                hp.straight = 0.0407
                if flush is True:
                    hp.straight_flush = 0.0025
        return hp

    def four_card_probability(self, card_a: Card, card_b: Card, card_c: Card, card_d: Card):
        """ calculate the probability of the hand with 4 cards delt of a 52 card deck
        @ card_a:[Card] the first card in the hand
        @ card_b:[Card] the second card in the hand
        @ card_c:[Card] the third card in the hand
        @ card_d:[Card] the fourth card in the hand
        """
        hp = HandProbability()
        # check for pairs
        card_value_set = set([card_a.rank.value, card_b.rank.value, card_c.rank.value, card_d.rank.value])
        if len(card_value_set) == 1: # all cards are the same value
            hp.pair = 1
            hp.two_pair = 0
            hp.three_of_a_kind = 1
            hp.four_of_a_kind = 1
            hp.full_house = 0
            hp.straight = 0
            hp.straight_flush = 0
            # we don't do 5 of a kind around here
        if len(card_value_set) == 2: # two pairs
            hp.pair = 1
            hp.two_pair = 1
        if len(card_value_set) == 3: # one pair
            hp.pair = 1

        flush = False
        card_suite_set = set([card_a.suit.value, card_b.suit.value, card_c.suit.value, card_d.suit.value])
        if len(card_suite_set) == 1: # all card are the same suit
            hp.flush = 0.18
            hp.full_house = 0
            flush = True

        # check for straights
        tmp = copy([card_a, card_b, card_c, card_d])
        tmp.sort(key=lambda x: x.rank.value)
        if abs(tmp[0] - tmp[1]) == 1 and abs(tmp[1] - tmp[2]) == 1 and abs(tmp[2] - tmp[3]) == 1:
            # for straights the probability is higher if the cards are in the middle of the values because
            # there are more cards that can be used to make the straight, if you have 2,3,4 the only cards
            # that can complete the straight are 5,6 but if you have 7,8,9 you can use 5,6,10,11 to complete
            # the straight.
            vals = [card_a.rank.value, card_b.rank.value, card_c.rank.value]
            if 2 in vals or 14 in vals:
                hp.straight = 0.083
                if flush is True:
                    hp.straight_flush = 0.0208
            else:
                hp.straight = 0.16
                if flush is True:
                    hp.straight_flush = 0.041

        return hp


class AiPokerPlayer(PokerPlayer):
    """ Class for an AI poker player """
    def __init__(self, name: str):
        super().__init__(name)
        self.human = False
        self.probability_to_match = 0.91
        self.probability_to_raise = 0.92
        self.probability_to_fold = 0.03


class PokerTable:
    """ Class for a poker table object """
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.players = [] # all players, human and AI
        self.human_players = []
        self.table_cards = Hand() # this is the flop, river cards
        self.pot = 0
        self.ante = 0
        self.current_table_bet = 0
        self.current_game_type = PokerGames.OMAHA
        self.game_state = GameState.PRE_DEAL
        self.dealer_position = 0
        self._human_has_bet = False  # used when betting in a ring to determine when to stop and get user input
        self._betting_order = []  # players organized so that the player to the left of the dealer is first (index 0)
        self._current_betting_position = 0  # used to track the current player in the betting order
        self._traversed_betting_order = False  # used to track if we have traversed the betting order in the current game
        self._first_game = True  # used to set the dealer position for the first game
        self._betting_round = 0  # used to track the current betting round, used for AI betting logic
        self._bet_around_blinds = True # used to track betting at the beginning of each game
        self._winning_player = None # type: PokerPlayer
        self._winning_hand = None # type: [Card]
        self._winning_rank = None # type: HandRank
        self._ai_players = []
        self._game_number = 0

    def next_game(self):
        """ if play has already begun at a table, calling this method will reset the table and prepare for a new game """
        gt = self.current_game_type
        anti = self.ante
        aip = self._ai_players
        hp = self.human_players
        self.new_game(gt, anti, aip, hp)

    def new_game(self, game_type: PokerGames, ante: int, ai_players: list, human_players: list):
        """ start a new game """
        for player in self.players: # type: PokerPlayer
            player.cards_in_hand.reset_hand()
            player.folded = False
            player.all_in = False

        self.table_cards.reset_hand()
        self.current_game_type = game_type
        self.deck = Deck()
        self.deck.shuffle()
        self.players = ai_players + human_players
        self.human_players = human_players
        self.pot = 0
        self.ante = ante
        self.current_table_bet = 0
        self.game_state = GameState.PRE_DEAL
        self._ai_players = ai_players
        self._betting_order = []
        self._bet_around_blinds = True
        self._traversed_betting_order = False
        self._winning_player = None
        self._winning_rank = None
        self._winning_hand = None
        self._game_number += 1

        self.current_betting_position_reset()

        log.message(f"Starting New Game: {game_type.name}")

        # create betting order based on dealer position
        if self._first_game is True:
            self._first_game = False
            # random.shuffle(self.players)
            self.dealer_position = random.randint(0, len(self.players)-1)
            log.message(f"First Game")
        else:
            self.dealer_position = (self.dealer_position + 1) % len(self.players)

        log.message(f"Dealer Position: {self.dealer_position}")

        self._betting_order = self.players[self.dealer_position + 1:] + self.players[:self.dealer_position + 1]
        log.message(f'players:       {[player.name for player in self.players]}')
        log.message(f"Betting order: {[player.name for player in self._betting_order]}")

        # get big and small blind bets , deal cards
        try:
            # small blind
            log.message(f'Small Blind: {ante} to {self._betting_order[0].name}')
            b1 = self._betting_order[0].place_bet(ante)

            # big blind
            log.message(f'Big Blind: {ante*2} to {self._betting_order[1].name}')
            b2 = self._betting_order[1].place_bet(ante * 2)
            self.pot = b1 + b2
            self.current_table_bet = b2

        except Exception as e:
            log.error(f'Player out of chips: {e}')  # edge case, if you run out of chips on the blinds, what are you doing at the table?

        self.game_state = GameState.INITIAL_DEAL

        # if game is omaha, deal 4 cards to each player
        if self.current_game_type == PokerGames.OMAHA:
            number_of_cards = 4
        else:
            number_of_cards = 2

        for player in self._betting_order:
            player.cards_in_hand.add_cards(self.deck.deal(number_of_cards))

        self.game_state = GameState.PRE_FLOP_BET

        self.progress_game('new_game')

        print(f"End method new_game")

    def progress_game(self, id: str):
        """ advance the game state """
        cbp = self._betting_order[self.current_betting_position_get()].name
        log.message(f"Progress Game: {self.game_state.name},id: {id}, Betting Round: {self._betting_round}, Current Betting Position: {cbp}, ")

        table_call = self._check_table_call()

        skip = table_call is True and self._betting_round != 0 # since progress game can be called from anywhere, protect from this case
        if skip is False: # skips betting if everyone's bet matches and it's not the first betting round
            if self._human_has_bet is False:

                self._bet_around_initial()
                self._human_has_bet = True
                table_call = False
            else:

                self._bet_around_final()
                self._human_has_bet = False
                self._betting_round += 1

                table_call = self._check_table_call() # check after the round of betting
                if table_call is False:
                    cbp = self._betting_order[self.current_betting_position_get()].name
                    gs = self.game_state
                    log.message(f"Bet Round: {self._betting_round}, for: {gs}, Current Betting Position: {cbp}, bet positions: {self._betting_order}")
                    self.progress_game('table_call_false')

        log.message(f"Check Table Call: {table_call}, Bet Round: {self._betting_round}, game state: {self.game_state}, ")
        if table_call is True: # ok to move to next round
            self.reset_current_player_bets()

            if self.game_state == GameState.PRE_FLOP_BET:
                self.game_state = GameState.POST_FLOP_BET
                self.table_cards.add_cards(self.deck.deal(3))
                log.message(f'Poker Game changed to POST_FLOP_BET, table cards: {self.table_cards}')
                self._check_players_left_reset_round_and_progress_game('post flop')

            elif self.game_state == GameState.POST_FLOP_BET:
                self.game_state = GameState.POST_TURN_BET
                self.table_cards.add_cards(self.deck.deal(1))
                log.message(f'Poker Game changed to POST_TURN_BET, table cards: {self.table_cards}')
                self._check_players_left_reset_round_and_progress_game('post turn')

            elif self.game_state == GameState.POST_TURN_BET:
                self.game_state = GameState.POST_RIVER_BET
                self.table_cards.add_cards(self.deck.deal(1))
                log.message(f'Poker Game changed to POST_RIVER_BET, table cards: {self.table_cards}')
                self._check_players_left_reset_round_and_progress_game('post river')

            # depending on where the human is in the betting order you will hit one of these two final cases
            elif self.game_state == GameState.POST_RIVER_BET:
                self.game_state = GameState.SHOWDOWN
                self._process_winner_round()

            elif self.game_state == GameState.SHOWDOWN:
                self._process_winner_round()

    def _bet_around_initial(self):
        """ iterate over players and make bets till you get to the human player """
        log.message(f"Bet around initial: {self._betting_order[self.current_betting_position_get()].name}")
        table_cards = self.table_cards
        game_state = self.game_state
        bet_order = self._betting_order

        self.current_betting_position_reset()

        if self._bet_around_blinds is True:
            self.current_betting_position_increment() # the first two players are the blinds
            self.current_betting_position_increment() # [a, b, c, d, e, f]
            cbp = self.current_betting_position_get()
            local_betting_order = bet_order[cbp:] + bet_order[:cbp]
            self._bet_around_blinds = False

        else:
            local_betting_order = bet_order[self.current_betting_position_get():]

        for player in local_betting_order:  # type: PokerPlayer
            if player.folded is False:
                if player.human is False:
                    # ai player
                    cbp = self.current_betting_position_get()
                    player.determine_bet(table_cards, self.current_table_bet, cbp, local_betting_order, game_state, self._betting_round)
                    total_bet = player.current_bet
                    if player.folded is False:
                        if total_bet != 0 and total_bet > self.current_table_bet:
                            self.current_table_bet = total_bet  # this is the only case that the tabel bet raises, else it stays
                        self.pot += total_bet
                    self.current_betting_position_increment()
                else:
                    # human player
                    break

    def _bet_around_final(self):
        """ iterate over player past the human player and make bets """
        log.message(f"Bet around final: {self._betting_order[self.current_betting_position_get()].name}")
        table_cards = self.table_cards
        local_betting_order = self._betting_order
        game_state = self.game_state
        rest_of_players = local_betting_order[self.current_betting_position_get():]
        for player in rest_of_players:  # type: PokerPlayer
            if player.folded is False:
                if player.human is False:
                    # ai player
                    cbp = self.current_betting_position_get()
                    player.determine_bet(table_cards, self.current_table_bet, cbp, local_betting_order,
                                               game_state, self._betting_round)
                    total_bet = player.current_bet
                    if player.folded is False:
                        if total_bet != 0 and total_bet > self.current_table_bet:
                            self.current_table_bet = total_bet  # this is the only case that the tabel bet raises, else it stays
                        self.pot += self.current_table_bet
                    self.current_betting_position_increment()
                else:
                    # human player
                    break

    def _process_winner_round(self):
        players_left = self._check_for_players_still_in_the_game()
        winner = self.get_winning_player_list(
            players_left)  # returns list like: [<player>, <HandRank>, <CardRank>, <Hand>]
        winning_player = winner[0]  # type: PokerPlayer
        log.message(f"Game Winner! {winning_player.name}, Hand Rank: {winner[1].name}, Winning Hand: ")
        winner[3].print_hand()
        self._winning_player = winning_player
        self._winning_rank = winner[1]
        self._winning_hand = winner[3]
        winning_player.chips += self.pot

    def _check_players_left_reset_round_and_progress_game(self, id: str):
        self._betting_round = 0
        self.current_table_bet = 0
        self._human_has_bet = False
        players_left = self._check_for_players_still_in_the_game()
        if len(players_left) > 1:
            self.progress_game(id)
        else:
            raise Exception(f"Winner by mass folding! {players_left[0]}")

    def _check_table_call(self) -> bool:
        """ check if all players have called the current table bet, used to determine if we can move to the next betting round """
        table_call = True
        for player in self._betting_order:  # type: PokerPlayer
            if player.current_bet == self.current_table_bet or player.folded is True:
                continue
            else:
                table_call = False
        return table_call

    def _check_for_players_still_in_the_game(self) -> list:
        """ check if there are players still in the game, returns a list of players that have not folded """
        still_playing = []
        for player in self._betting_order:
            if player.folded is False:
                still_playing.append(player)
        return still_playing

    def get_winning_player_list(self, players: list) -> list:
        """ check the winning hand, returns the player with the winning hand
        @ players: a list of players, this is used to determine the winning hand
        @ return: represents the winner with a list like: [<player>, <HandRank>, <CardRank>, <Hand>]
        raises an exception in the event of a tie
        raises an exception if the list of players is less than 2, since we need at least two players to determine a winner"""
        # have to iterate over all players and all combinations of two hand cards and three table cards

        if len(players) < 2:
            raise Exception(f"Not enough players to determine a winner, need at least 2, got players {players}")

        hand_class = Hand()
        player_hands = [] # like: [<player>, <HandRank>, <CardRank>, <Hand>]
        for player in players: # type: PokerPlayer

            if player.folded is False: # protect against folded players winning game

                # get all the combinations of cards
                hand_pairs = list(itertools.combinations(player.cards_in_hand.cards, 2))
                table_triplets = list(itertools.combinations(self.table_cards.cards, 3))

                # print(f"combinations for {player.name}, hand: {player.cards_in_hand.get_string_hand()}, ")
                # for pair in hand_pairs:
                #     print(pair)
                #
                # for triplet in table_triplets:
                #     print(triplet)

                # track the high values in the loop
                running_rank = HandRank.INITIAL
                running_high_card = Card(CardRank.TWO, Suit.DIAMONDS)
                running_high_hand = None
                running_list = [] # like: [<player>, <HandRank>, <CardRank>, <Hand>]

                for hand_pair in hand_pairs:
                    for table_triplet in table_triplets:

                        cards_5 = list(hand_pair) + list(table_triplet)
                        hand_class.reset_hand()
                        hand_class.add_cards(cards_5)
                        ranks = hand_class.score_5_or_7_card_hand() # this returns all ranks achieved so need to get max
                        high_rank = max(ranks) # type: HandRank
                        high_card = max(hand_class.winning_cards) # type: Card
                        # print(f"EEE{high_rank}, cards: {cards_5}, {player.name},  ")

                        if high_rank.value > running_rank.value:
                            running_rank = deepcopy(high_rank)
                            running_high_card = deepcopy(high_card)
                            running_high_hand = deepcopy(hand_class)
                            running_list = [player, running_rank, running_high_card, running_high_hand]
                            log.message(f"New Winning Hand: {running_list}, player: {player.name}, ")

                if len(running_list) != 0:
                    player_hands.append(running_list)
                hand_class.reset_hand()

        # there is a much more concise way to do this, but I would like to see all the hands before doing the final score
        # for hand in player_hands:
        #     log.message(f"XXX{hand[3]}, {hand[1]}, {hand[0].name} ")

        winning_player_l = player_hands[0] # pick the first player as the winner to start with
        tie_l = None
        for l in player_hands[1:]: # type: list
            player, hand_rank, high_card, hand = l # unpack the list

            if hand_rank.value > winning_player_l[1].value:
                winning_player_l = l # new winner
                tie_l = None

            # check for tie
            elif hand_rank.value == winning_player_l[1].value and high_card.rank.value > winning_player_l[2].rank.value:
                winning_player_l = l # new winner
                tie_l = None

            elif hand_rank.value == winning_player_l[1].value and high_card.rank.value == winning_player_l[2].rank.value:

                    if hand_rank.value == HandRank.FULL_HOUSE.value:
                        # if we have a full house, we need to check the three of a kind
                        hcv = high_card.rank.value
                        hcc = 0
                        for card in hand.cards:
                            if card.rank.value == hcv:
                                hcc += 1
                        if hcc == 3: # this hand is the winner
                            winning_player_l = l # new winner
                    else:
                        tie_l = l # no winner its a tie
            # else nothing

        if tie_l is not None: # check if the current winning hand is higher than the tie hand
                log.message(f"There is a tie: {winning_player_l} ")
                log.message(f"There is a tie: {tie_l} ")
                raise Exception(f"There is a tie between {winning_player_l[0].name} and {tie_l[0].name}, "
                                f"cards: {winning_player_l[3].get_string_hand()} and {tie_l[3]}")
        else:
            return winning_player_l

    def reset_current_player_bets(self):
        """ sets the current bet for all the palyers to 0, used to reset the bets after a betting round """
        for player in self.players:  # type: PokerPlayer
            player.current_bet = 0

    def get_game_state_string(self):
        """ Prints an ascii representation of the game state """
        if self._winning_player is None:
            string = f"-------------Flop Cards----------\n"
            string += self.table_cards.get_string_hand()
            string += f"\n"

            string += f"|   Player    | Dealer | Folded | Chips   | Bet |\n"
            string += f"-------------------------------------------------\n"
            for idx, player in enumerate(self.players):

                folded = 'No '
                if player.folded:
                    folded = 'Yes'

                dealer = ' '
                if idx == self.dealer_position:
                    dealer = 'X'
                # add the fields to the chart, match the width of the header

                l1 = 12-len(player.name)
                st = ' ' * l1
                l2 = 8-len(str(player.chips))
                st2 = ' ' * l2
                l3 = 4-len(str(player.current_bet))
                st3 = ' ' * l3

                string += f"| {player.name}{st}|   {dealer}    |   {folded}  | {player.chips}{st2}| {player.current_bet}{st3}|\n"

            string += f"\n"
            for player in self.human_players:  # type: PokerPlayer
                string += f"Player: {player.name} --- chips: {player.chips} \n"
                string += player.cards_in_hand.get_string_hand()
        else: # create a winning player string that shows the table hand, then the winner and stats
            string = f"-------------Flop Cards----------\n"
            string += self.table_cards.get_string_hand()
            string += f"\n"
            string += f"Winner: {self._winning_player.name}, Hand Rank: {self._winning_rank.name}, Winning Hand: "
            string += f"\n"
            string += self._winning_hand.get_string_hand()
            string += f"\n"
            string += f"|   Player    | Dealer | Folded | Chips   | Bet |\n"
            string += f"-------------------------------------------------\n"
            for idx, player in enumerate(self.players):

                folded = 'No '
                if player.folded:
                    folded = 'Yes'

                dealer = ' '
                if idx == self.dealer_position:
                    dealer = 'X'
                # add the fields to the chart, match the width of the header

                l1 = 12-len(player.name)
                st = ' ' * l1
                l2 = 8-len(str(player.chips))
                st2 = ' ' * l2
                l3 = 4-len(str(player.current_bet))
                st3 = ' ' * l3

                string += f"| {player.name}{st}|   {dealer}    |   {folded}  | {player.chips}{st2}| {player.current_bet}{st3}|\n"

            string += f"\n"
            for player in self.human_players:  # type: PokerPlayer
                string += f"Player: {player.name} --- chips: {player.chips} \n"
                string += player.cards_in_hand.get_string_hand()
        return string

    def get_human_player(self) -> PokerPlayer:
        """ return the human player """
        return self.human_players[0]

    def  human_bet(self, amount: int, human_player_position=0):
        """ place a bet
        @ amount: the amount to bet
        @ human_player_position: the position of the human player in the human player list, 0 for 1 human """
        try:

            player = self.human_players[human_player_position]  # type: PokerPlayer # in the future, maybe more than one

            if player.all_in is False and player.folded is False:

                total_bet = amount + player.current_bet

                if total_bet >= self.current_table_bet:

                    if amount > player.chips: # go all in
                        amount = player.chips # adjust the amount to the chips left
                        player.place_bet(player.chips)
                        player.all_in = True

                    player.place_bet(amount)

                    if player.folded is False and player.all_in is False:
                        self.current_table_bet = player.current_bet
                    self.pot += self.current_table_bet

                    log.message(f'Human Player: {player.name} placing bet: {amount} ----------------------------')

                else: # need to match the table bet
                    raise Exception(f"Player {player.name} cannot bet {total_bet}, current bet is {self.current_table_bet}, "
                                    f"you must at least match the current bet")

        except Exception as ex:
            raise Exception(f"Poker Table: bet({amount}) failed: {ex}")

        # only increment if no exception
        self.current_betting_position_increment()

    def current_betting_position_increment(self):
        """ increment the current betting position, tracks the traversed betting order """
        self._current_betting_position += 1
        if self._current_betting_position >= len(self._betting_order):
            self._current_betting_position = 0
            self._traversed_betting_order = True

    def current_betting_position_reset(self):
        """ called after all playes have been made for the current betting round, resets the betting position
        and the traversed betting order flag """
        self._current_betting_position = 0
        self._traversed_betting_order = True

    def current_betting_position_get(self) -> int:
        """ return the current betting position """
        return self._current_betting_position

    def get_game_number(self) -> int:
        """ return the current game number """
        return self._game_number


# brute force probability calculators ------------------------------------------

class ProbabilityCalculator:
    """ Class for calculating the probability of poker hands
    Warning: Uses multiprocessing pool, may run slow in debug mode
    """
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.hand = Hand()
        self.hand_probability = HandProbability()
        self._process_count = int(os.process_cpu_count() / 2) # if you really need to crank, div by 1

    def _calculate_n_card_deal_n_prob(self, iterations: int, cards_in_hand: list, deal_n_cards: int, rank: HandRank = HandRank.PAIR):
        """ given the n cards passed, calculate the probability of getting a hand_rank after dealing n cards
        this is a private method passed to a multiprocessing pool"""
        num_of_cards = len(cards_in_hand) + deal_n_cards
        if num_of_cards != 5 and num_of_cards != 7:
            msg = f"Invalid number of cards to calculate probability: {num_of_cards}, must be 5 or 7"
            raise Exception(msg) # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        hands_with_match = 0
        partial_deck = PartialDeck(cards_in_hand) # this makes a deck without the cards in hand so you dont have to remove them in each loop
        hand = self.hand
        for _i in range(iterations):
            partial_deck.reset_deck()
            partial_deck.shuffle()
            hand.reset_hand()
            hand.add_cards(cards_in_hand + partial_deck.deal(deal_n_cards))
            # if you get a full house but are checking the probability of a pair, you need to see all ranks for the hand
            # not just the highest rank
            ranks = set(hand.score_5_or_7_card_hand())
            if rank in ranks:
                hands_with_match += 1
        return hands_with_match / iterations

    def calculate_n_card_hand_probability(self, iterations: int, cards_in_hand: list, deal_n_cards: int, hand_rank: HandRank):
        """ calculate the probability of getting a hand_rank with a given number of cards in hand and being delt n cards
        the sum of the cards in hand and the cards delt must be 5 or 7 ( to either have a 5 card poker hand or a 7 card poker hand)
        @param: iterations: the number of iterations to run
        @param:[list of cards] cards_in_hand: the cards in the hand
        @param: deal_n_cards: the number of cards to deal
        @param: hand_rank: the hand rank to calculate the probability of
        @return:[float] the probability of getting the hand_rank
        """
        with mp.Pool(self._process_count) as pool:
            arg_list = [(int(iterations/self._process_count), cards_in_hand, deal_n_cards, hand_rank)]*self._process_count
            results = pool.starmap(self._calculate_n_card_deal_n_prob, arg_list)
            print(f"Results: {results}")
            no_zeros = [x for x in results if x != 0] # for hands with low probability you can get zeros here, remove them before averaging
            if len(no_zeros) == 0: # all processes returned zero
                return 0 # for example if you have a pair the probability of a straight flush is zero
            mean = sum(no_zeros) / len(no_zeros) # average the results from each process, may want to look at the variance
            return mean

    def _calculate_5_card_hand_prob(self, iterations: int, rank: HandRank = HandRank.PAIR):
        """ calculate the probability of a five card hand, this private method is passed to the multiprocessing pool """
        hands_with_match = 0
        deck = self.deck
        hand = self.hand
        for _i in range(iterations):
            deck.reset_deck()
            deck.shuffle()
            hand.reset_hand()
            hand.add_cards(deck.deal(5))
            hand.score_5_or_7_card_hand()
            if hand.hand_rank == rank:
                hands_with_match += 1
        return hands_with_match / iterations

    def calculate_hand_probability(self, iterations: int = 1e6, hand_rank: HandRank = HandRank.PAIR):
        """ calculates the probability of getting a hand_rank (pair, flush, etc...) when delt five cards from a 52 card deck
        this is a brute force method to verify that this system is fair (has the same probabilities as a real poker game)
        The output of this method should match the 5 card hand probabilities that are known for poker (see the internet)
        @param: iterations: the number of iterations to run
        @param: hand_rank: the hand rank to calculate the probability of
        @return: [float] the probability of getting the hand_rank if delt 5 cards from a 52 card deck
        """
        with mp.Pool(self._process_count) as pool:
            arg_list = [(int(iterations/self._process_count), hand_rank)]*self._process_count # divides the work for each process
            results = pool.starmap(self._calculate_5_card_hand_prob, arg_list) # maps the result of each process to a list
            print(f"Results: {results}")  # interesting to see the results of each process
            no_zeros = [x for x in results if x != 0] # for hands with low probability you can get zeros here, remove them before averaging
            mean = sum(no_zeros) / len(no_zeros) # average the results from each process, may want to look at the variance
            return mean





