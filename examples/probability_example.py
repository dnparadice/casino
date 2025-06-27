import time
import poker
from poker import HandRank

if __name__ == '__main__':

    run_section = 2 # pick a section to run

    if run_section == 1: # this section calculates the probability of a hand rank

        # //////////// edit these values to test different hand ranks and iterations ////////////
        hand_rank = poker.HandRank.STRAIGHT_FLUSH
        iterations = int(1e3) # typical is 1e6 for all hands less than a straight flush, need to do 1e7 for straight flush
        # //////////////////////////////////////////////////////////////////////////////////////

        pc = poker.ProbabilityCalculator()
        hp = poker.HandProbability()
        print(f"Starting '{hand_rank.name}' Probability Calculation for '{iterations:,d}' iterations")

        # # try using a single process, the result of this was ~19s for 1M iterations for 2019MBP w/ 16cores (using 8 processes)
        # t1 = time.time()
        # pair_prob = pc._calculate_5_card_hand_prob(iterations, hand_rank) # this private method is what is passed to each process in the pool
        # t2 = time.time()
        # expected_prob = hp.get_probability_for_rank(hand_rank)
        # print(f"Calculated {hand_rank.name} Probability: {pair_prob}, Expected Probability: {expected_prob}, error %: {abs(pair_prob - expected_prob) * 100}")
        # print(f"Time to calculate: {t2 - t1}s")

        # try using multiprocessing pool, the result of this was 3s for 1M iterations for 2019MBP w/ 16cores (using 8 processes)
        t1 = time.time()
        prob = pc.calculate_hand_probability(iterations, hand_rank)
        t2 = time.time()
        expected_prob = hp.get_probability_for_rank(hand_rank)
        error_percent = abs(prob - expected_prob)/expected_prob * 100
        print(f"Calculated {hand_rank.name} Probability: {prob}, Expected Probability: {expected_prob}, error %: {error_percent}")
        print(f"Time to calculate: {t2 - t1}s")

    if run_section == 2: # this section calculates the hand rank given n pocket cards

        # //////////// edit these values to test different hand ranks and iterations ////////////
        hand_rank = poker.HandRank.STRAIGHT_FLUSH
        iterations = int(1e6)
        # these are your pocket cards
        cards = [poker.Card(poker.CardRank.EIGHT, poker.Suit.CLUBS),
                 poker.Card(poker.CardRank.SEVEN, poker.Suit.CLUBS),]
        # //////////////////////////////////////////////////////////////////////////////////////
        pc = poker.ProbabilityCalculator()
        hp = poker.HandProbability()
        print(f"Starting '{hand_rank.name}' Probability Calculation for '{iterations:,d}' iterations")

        # prob = pc.calculate_n_card_hand_probability(iterations, cards, 3, hand_rank)
        prob = pc.calculate_n_card_hand_probability(iterations, cards, 3, hand_rank)

        expected_prob = hp.get_probability_for_rank(hand_rank)
        delta = prob - expected_prob
        print(f"Calculated {hand_rank.name} Probability: {prob}, Five Card Probability: {expected_prob}, Delta: {delta}")


