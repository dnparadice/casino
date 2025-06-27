import unittest
from random import shuffle

import poker
import player
import casino


class MyTestCase(unittest.TestCase):
    def test_hand_rank_pair(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.TWO, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.TWO, poker.Suit.HEARTS),
            poker.Card(poker.CardRank.THREE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.ACE, poker.Suit.CLUBS),
            poker.Card(poker.CardRank.FIVE, poker.Suit.SPADES),
        ]
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value

        self.assertEqual(rank, poker.HandRank.PAIR.value)  # add assertion here

    def test_hand_rank_two_pair(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.QUEEN, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.QUEEN, poker.Suit.HEARTS),
            poker.Card(poker.CardRank.THREE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.THREE, poker.Suit.CLUBS),
            poker.Card(poker.CardRank.FIVE, poker.Suit.SPADES),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.TWO_PAIR.value)

    def test_hand_rank_three_of_a_kind(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.TEN, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.TEN, poker.Suit.HEARTS),
            poker.Card(poker.CardRank.TEN, poker.Suit.CLUBS),
            poker.Card(poker.CardRank.THREE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.FIVE, poker.Suit.SPADES),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.THREE_OF_A_KIND.value)

    def test_hand_rank_four_of_a_kind(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.TWO, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.TWO, poker.Suit.HEARTS),
            poker.Card(poker.CardRank.TWO, poker.Suit.CLUBS),
            poker.Card(poker.CardRank.TWO, poker.Suit.SPADES),
            poker.Card(poker.CardRank.FIVE, poker.Suit.SPADES),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.FOUR_OF_A_KIND.value)

    def test_hand_rank_full_house(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.TWO, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.TWO, poker.Suit.HEARTS),
            poker.Card(poker.CardRank.TWO, poker.Suit.CLUBS),
            poker.Card(poker.CardRank.THREE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.THREE, poker.Suit.SPADES),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.FULL_HOUSE.value)

    def test_hand_rank_straight(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.SEVEN, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.THREE, poker.Suit.HEARTS),
            poker.Card(poker.CardRank.FOUR, poker.Suit.CLUBS),
            poker.Card(poker.CardRank.FIVE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.SIX, poker.Suit.SPADES),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.STRAIGHT.value)

    def test_hand_rank_straight_flush(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.TEN, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.QUEEN, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.KING, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.JACK, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.ACE, poker.Suit.DIAMONDS),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.STRAIGHT_FLUSH.value)

    def test_hand_rank_flush(self):
        hand = poker.Hand()
        cards = [
            poker.Card(poker.CardRank.TWO, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.THREE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.FOUR, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.FIVE, poker.Suit.DIAMONDS),
            poker.Card(poker.CardRank.SEVEN, poker.Suit.DIAMONDS),
        ]
        shuffle(cards)
        hand.add_cards(cards)
        hand.score_5_or_7_card_hand()
        rank = hand.hand_rank.value
        self.assertEqual(rank, poker.HandRank.FLUSH.value)



if __name__ == '__main__':
    unittest.main()

