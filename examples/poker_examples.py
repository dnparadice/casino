""" ----------------- Example Code ----------------- """

from poker import Deck, Hand, Card, CardRank, Suit, PokerTable, PokerGames, AiPokerPlayer, GameState

if __name__ == '__main__':

    case = 7 # Run this case

    # basic hands ------------------------------------------
    if case == 1:
        deck = Deck()
        deck.shuffle()
        hand1 = Hand()

        define_cards = False # either define the hand or deal from the deck
        if define_cards is True:
            tmp_hand = [Card(CardRank.TWO, Suit.HEARTS),
                        Card(CardRank.KING, Suit.DIAMONDS),
                        Card(CardRank.FOUR, Suit.HEARTS),
                        Card(CardRank.QUEEN, Suit.HEARTS),]
            hand1.add_cards(tmp_hand)
        else:
            hand1.add_cards(deck.deal(4))

        hand1.print_hand()
        hand1.score_partial_hand()

        hand2 = Hand()
        hand2.add_cards(deck.deal(7))
        hand2.print_hand()
        hand2.score_5_or_7_card_hand()

        hand3 = Hand()
        hand3.add_cards(deck.deal(7))
        hand3.print_hand()
        hand3.score_5_or_7_card_hand()

    # poker table ------------------------------------------
    if case == 2:
        table = PokerTable()
        players = ['Borlab', 'Kuvpx', 'Frool', 'MoOm', 'Vastrrian']
        table.new_game(PokerGames.OMAHA, 5, )

    # test scoring full hand ------------------------------------------
    if case == 3:
        hand = Hand()
        cards = [Card(CardRank.SEVEN, Suit.DIAMONDS),
                 Card(CardRank.EIGHT, Suit.DIAMONDS),
                 Card(CardRank.NINE, Suit.DIAMONDS),
                 Card(CardRank.TEN, Suit.DIAMONDS),
                 Card(CardRank.THREE, Suit.DIAMONDS),]
        hand.add_cards(cards)
        ranks = hand.score_5_or_7_card_hand(True)
        print(ranks)

    # test poker player ------------------------------------------
    if case == 4:
        hand = Hand()
        cards = [Card(CardRank.SEVEN, Suit.CLUBS),
                 Card(CardRank.SEVEN, Suit.DIAMONDS),
                 Card(CardRank.EIGHT, Suit.HEARTS),
                 Card(CardRank.KING, Suit.CLUBS),
                 ]
        hand.add_cards(cards)
        player = AiPokerPlayer('Duchl')
        prob = player.get_n_card_probability(cards)
        delta = prob.get_delta_probability()
        delta_sum = prob.get_delta_probability_sum()
        print(f"Delta: {delta}, Delta Sum: {delta_sum}")

    # test poker bet ------------------------------------------
    if case == 5:
        ai_player = AiPokerPlayer('!Humon')
        hand = Hand()
        cards = [Card(CardRank.SEVEN, Suit.CLUBS),
                 Card(CardRank.EIGHT, Suit.HEARTS),
                 ]
        hand.add_cards(cards)
        ai_player.cards_in_hand = hand
        other_players = [AiPokerPlayer('Bjort'), AiPokerPlayer('Cromulen'), AiPokerPlayer('Dorp')]
        table_cards = Hand()
        current_bet = 4
        bet_position = 1
        gs = GameState.PRE_FLOP_BET
        bet_amount = ai_player.determine_bet(table_cards, current_bet, bet_position, other_players, gs, 0)

    # test determine winner ------------------------------------------
    # create five players with good hands and determine the winner using the poker table methdo get_winning_player_list
    if case == 6:
        table = PokerTable()
        players = [AiPokerPlayer('Srgevan'),
                   AiPokerPlayer('Gamogoc'),
                   AiPokerPlayer('Pqrset'),
                   AiPokerPlayer('eF Ngsxt'),
                   AiPokerPlayer('Vrstepyn')]

        deck = Deck()
        deck.shuffle()
        # deal 4 cards to each player and 5 cards to the table
        for player in players:
            player.cards_in_hand.add_cards(deck.deal(4))
            print(f"{player.name} hand: {player.cards_in_hand}")
        tc = deck.deal(5)
        print(f"Table Cards: {tc}")
        table.table_cards.add_cards(tc)

        # score the hands
        winner = table.get_winning_player_list(players)
        print(f"Winner: {winner}")

    # test hand score for known hand -----------------------------------
    if case == 7:
        good_hand = AiPokerPlayer('GoodHandLuke')
        cards = [Card(CardRank.SEVEN, Suit.DIAMONDS),
                 Card(CardRank.THREE, Suit.DIAMONDS),
                 Card(CardRank.SEVEN, Suit.HEARTS),
                 Card(CardRank.EIGHT, Suit.HEARTS),]
        good_hand.cards_in_hand.add_cards(cards)

        ok_hand = AiPokerPlayer('Ok')
        cards = [Card(CardRank.THREE, Suit.SPADES),
                 Card(CardRank.TWO, Suit.HEARTS),
                 Card(CardRank.KING, Suit.DIAMONDS),
                 Card(CardRank.TEN, Suit.HEARTS),]
        ok_hand.cards_in_hand.add_cards(cards)

        cards = [Card(CardRank.QUEEN, Suit.HEARTS),
                 Card(CardRank.THREE, Suit.CLUBS),
                 Card(CardRank.EIGHT, Suit.CLUBS),
                 Card(CardRank.EIGHT, Suit.DIAMONDS),
                 Card(CardRank.QUEEN, Suit.SPADES),]

        table = PokerTable()
        table.table_cards.add_cards(cards)
        winner = table.get_winning_player_list([good_hand, ok_hand])
        print(f"Winner: {winner}")














