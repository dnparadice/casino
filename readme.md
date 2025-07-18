# A Casino Game Simulation Tool

<img src="media/PyCasino - Poker 20250614.jpg" alt="Casino UI - Poker" width="800" height="auto">


The goal of this app is to simulate playing casino games to help players understand probability and odds.

A secondary goal is to make AI opponents that are human like in their style and faults of play. 

### Features
- Brute force calculations of hand probabilities using Multiprocessing 

### The UI

To launch the UI grab the repo and run main.py. This will launch the UI and you can select between poker 
and roulette (others coming later .... much later). 

#### Poker

On the poker tab press the "Start Poker Game" button
the game will progress until it is time for you "Humon" to play. You can choose to bet check or fold. The game will
proceded untill a winner is determined then pressing "Start Poker Game" will move to the next game. 

1) The cards on the table (flop cards) are shown on the top and your cards "Humon" are 
shown on the bottom. The middle grid shows the state of game play for each player. 
2) When launching the app for the first time the dealer position will be chosen at random, for each subsequent game
the dealer will be the next player on the list (progressing top to bottom)
3) When placing a bet you will see that there may already be a bet from a previous betting round so you will have 
to do some math to determine if you want to match the current bet or raise. The bet entered in the field is in addition 
to the current bet so if you are the blind and bet 2 and the betting  comes to you and is 6, and you enter 6 as a bet you will 
be raising the bet buy 2 since 2+6 = 8 making the bet to the next player 8.

### The Code - CLI use
The code makes use of OOP to create classes for casinos, player, cards, decks, etc. If you are so inclined
you can use the code on the command line to play the same game as in the UI with ASCII art for the cards. 

```
08:07:24.689::BET:: Fluub prob sum: 3.8110444020000016, new bet: 0, current bet : 0, current table bet: 0, round: 0, raise: False, fold: False,  multiplier: 0.2, POST_RIVER_BET, hand: [(♥ SEVEN ♥), (♦ SEVEN ♦), (♥ TEN ♥), (♠ JACK ♠)],
08:07:24.689::Check Table Call: True, Bet Round: 1, game state: GameState.POST_RIVER_BET, 
08:07:24.689::New Winning Hand: [Bjort, 20 chips, (♣ QUEEN ♣) (♥ KING ♥) (♣ FIVE ♣) (♠ KING ♠) , current bet: 0, folded: False, <HandRank.HIGH_CARD: 1>, (♥ KING ♥), HandHandRank.HIGH_CARD[(♣ QUEEN ♣), (♥ KING ♥), (♠ FIVE ♠), (♣ THREE ♣), (♦ JACK ♦)]], player: Bjort, 
08:07:24.690::New Winning Hand: [Bjort, 20 chips, (♣ QUEEN ♣) (♥ KING ♥) (♣ FIVE ♣) (♠ KING ♠) , current bet: 0, folded: False, <HandRank.PAIR: 2>, (♣ FIVE ♣), HandHandRank.PAIR[(♣ QUEEN ♣), (♣ FIVE ♣), (♠ FIVE ♠), (♣ THREE ♣), (♦ JACK ♦)]], player: Bjort, 
08:07:24.691::New Winning Hand: [Fluub, 16 chips, (♥ SEVEN ♥) (♦ SEVEN ♦) (♥ TEN ♥) (♠ JACK ♠) , current bet: 0, folded: False, <HandRank.PAIR: 2>, (♥ SEVEN ♥), HandHandRank.PAIR[(♥ SEVEN ♥), (♦ SEVEN ♦), (♠ FIVE ♠), (♣ THREE ♣), (♦ JACK ♦)]], player: Fluub, 
08:07:24.692::Game Winner! Fluub, Hand Rank: PAIR, Winning Hand: 
+--------+ +--------+ +--------+ +--------+ +--------+ 
|7       | |7       | |5       | |3       | |J       | 
|        | |        | |        | |        | |        | 
|    ♥   | |    ♦   | |    ♠   | |    ♣   | |    ♦   | 
|        | |        | |        | |        | |        | 
|       7| |       7| |       5| |       3| |       J| 
+--------+ +--------+ +--------+ +--------+ +--------+ 
```

#### Roulette

The Roulette game allows you to run many simulations of the game very fast to see how betting 'strategies' work. You
can make number bets, and bet across groups of numbers as on an actual roulette table. The results of all the spins are 
displayed on the UI and a plot is generated to show the history of your cash in hand (Bank).

<img src="media/roulette and plot 20250715.jpg" alt="Casino UI - Poker" width="800" height="auto">


### todos
- need to get the probability of other players getting a better hand 