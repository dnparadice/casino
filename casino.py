import ast
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.lines import lineStyles

from logger import Logger
import poker
import roulette

log = Logger()


class Casino:

    def __init__(self):
        self.poker_table = poker.PokerTable()
        self.roulette_table = roulette.RouletteTable()
        self.ui = UserInterface(self)

    def start(self):
        self.ui.mainloop()


class UserInterface(tk.Tk):

    def __init__(self, casino: Casino):
        super().__init__()
        self.casino = casino
        self.title("Casino")
        self.geometry("800x700")

        # add large text filed with monospaced font to display game messages
        self.game_messages = tk.Text(self, font=("Courier", 12))
        self.game_messages.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.poker_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.poker_tab, text="Poker")

        self.roulette_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.roulette_tab, text="Roulette")

        self.notebook.bind("<<NotebookTabChanged>>", self._notebook_tab_changed)

        self.poker_table_frame = ttk.Frame(self.poker_tab)
        self.poker_table_frame.pack(fill=tk.BOTH, expand=True)

        # ---------- Roulette Stuff --------------------

        # create grid in the roulette tab and add fields for entering the bank amount, the bet amount, the bets and a start button

        # left frame
        self.roulette_left_frame = ttk.Frame(self.roulette_tab)
        self.roulette_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.roulette_entry_bank_amount = ttk.Entry(self.roulette_left_frame,)
        self.roulette_entry_bank_amount.insert(0, '777')
        self.roulette_entry_bank_amount.grid(row=0, column=0, padx=0, pady=10)
        self.roulette_label_bank_amount = ttk.Label(self.roulette_left_frame, text="Bank Amount")
        self.roulette_label_bank_amount.grid(row=0, column=1, padx=0, pady=10)

        self.roulette_entry_bet_amount = ttk.Entry(self.roulette_left_frame)
        self.roulette_entry_bet_amount.insert(0, '10')
        self.roulette_entry_bet_amount.grid(row=1, column=0, padx=10, pady=10)
        self.roulette_label_bet_amount = ttk.Label(self.roulette_left_frame, text="Bet Amount")
        self.roulette_label_bet_amount.grid(row=1, column=1, padx=10, pady=10)

        self.roulette_entry_bet_positions = ttk.Entry(self.roulette_left_frame)
        self.roulette_entry_bet_positions.insert(0, '12,0,(3,4)')
        self.roulette_entry_bet_positions.grid(row=2, column=0, padx=10, pady=10)
        self.roulette_label_bet_positions = ttk.Label(self.roulette_left_frame, text="Bet Positions (e.g. 12,00,3)")
        self.roulette_label_bet_positions.grid(row=2, column=1, padx=10, pady=10)

        self.roulette_entry_number_of_spins = ttk.Entry(self.roulette_left_frame)
        self.roulette_entry_number_of_spins.insert(0, '100')
        self.roulette_entry_number_of_spins.grid(row=3, column=0, padx=10, pady=10)
        self.roulette_label_number_of_spins = ttk.Label(self.roulette_left_frame, text="Number of Spins")
        self.roulette_label_number_of_spins.grid(row=3, column=1, padx=10, pady=10)

        # add boolean selector for American or European roulette
        self.roulette_european_var = tk.BooleanVar(value=True)
        self.roulette_european_checkbutton = ttk.Checkbutton(self.roulette_left_frame, text="European Roulette", variable=self.roulette_european_var)
        self.roulette_european_checkbutton.grid(row=4, column=0, padx=10, pady=10, columnspan=2)


        # right frame
        self.roulette_right_frame = ttk.Frame(self.roulette_tab)
        self.roulette_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


        # create button "run simulation"
        self.roulette_run_simulation_button = ttk.Button(self.roulette_right_frame, text="Run Simulation", command=self.run_roulette_simulation)
        self.roulette_run_simulation_button.pack(pady=10)

        # create a text field to display "Final Bank Amount" after the simulation

        self.roulette_final_bank_label = ttk.Label(self.roulette_right_frame, text="Final Bank Value: ")
        self.roulette_final_bank_label.pack(pady=10)
        self.roulette_final_bank_value = ttk.Label(self.roulette_right_frame, text="0")
        self.roulette_final_bank_value.pack(pady=10)

        # create a text field to display the "Max Bank Value"
        self.roulette_max_bank_label = ttk.Label(self.roulette_right_frame, text="Max Bank Value: ")
        self.roulette_max_bank_label.pack(pady=10)
        self.roulette_max_bank_value = ttk.Label(self.roulette_right_frame, text="0")
        self.roulette_max_bank_value.pack(pady=10)

        # create a text field to display the "Min Bank Value"
        self.roulette_min_bank_label = ttk.Label(self.roulette_right_frame, text="Min Bank Value: ")
        self.roulette_min_bank_label.pack(pady=10)
        self.roulette_min_bank_value = ttk.Label(self.roulette_right_frame, text="0")
        self.roulette_min_bank_value.pack(pady=10)

        # ---------- Poker Stuff -----------------------

        # add button to start a new poker game
        self.start_poker_button = ttk.Button(self.poker_tab, text="Start Poker Game", command=self.start_poker)

        # add betting buttons
        self.bet_button = ttk.Button(self.poker_tab, text="Bet", command=self.button_bet)

        # add bet amount entry
        self.bet_amount = ttk.Entry(self.poker_tab)

        self.check_button = ttk.Button(self.poker_tab, text="Check", command=self.button_check)
        self.fold_button = ttk.Button(self.poker_tab, text="Fold", command=self.button_fold)
        # place all buttons on grid along the bottom of the frame
        self.start_poker_button.pack(side=tk.LEFT)
        self.bet_amount.pack(side=tk.LEFT)
        self.bet_button.pack(side=tk.LEFT)
        self.check_button.pack(side=tk.LEFT)
        self.fold_button.pack(side=tk.LEFT)

        self.poker_table_label = ttk.Label(self.poker_table_frame, text="Poker Table")
        self.poker_table_label.pack()

        self.pot = ttk.Label(self.poker_table_frame, text="Pot: 0")
        self.pot.pack()
        self.current_bet = ttk.Label(self.poker_table_frame, text="Current Bet: 0")
        self.current_bet.pack()
        self.poker_game_state = ttk.Label(self.poker_table_frame, text="Game State")
        self.poker_game_state.pack()


    def _notebook_tab_changed(self, event):
        """ Handles the notebook tab change event to update the game messages """
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            # Poker tab selected
            self.game_messages.replace("1.0", tk.END, self.casino.poker_table.get_game_state_string())
            self.update_pot_and_current_bet_display()
        elif current_tab == 1:
            self.game_messages.replace("1.0", tk.END, self.casino.roulette_table.get_game_state_string())

    # -------------------------------------------------------------------------------------
    #                                 Roulette
    # -------------------------------------------------------------------------------------


    def run_roulette_simulation(self):
        """ Runs a simulation of the roulette game based on user input """
        try:

            # create a new table based on user settings
            use_euro = self.roulette_european_var.get()
            roulette_table = self.casino.roulette_table = roulette.RouletteTable(european=use_euro)
            bank_amount = float(self.roulette_entry_bank_amount.get())

            # add a player to the roulette table
            p_name = 'Bob'
            player = roulette.RoulettePlayer(p_name)
            player.chips += bank_amount
            roulette_table.add_player(player)

            # setup the game
            number_of_spins = int(self.roulette_entry_number_of_spins.get())
            for spin in range(number_of_spins):
                bet_amount = self.roulette_entry_bet_amount.get()
                bet_positions = self.roulette_entry_bet_positions.get()
                roulette_table.table_place_bet(bet_positions, bet_amount, player_name=p_name)
                roulette_table.spin_the_wheel()

                # display the results in the game messages text field
                self.game_messages.replace("1.0", tk.END, roulette_table.get_game_state_string())

            bank = player.running_bank

            # plot the history of the bank
            plot_label = f"{p_name}'s Bank History  --  Min: {min(bank):.2f}  --  Max: {max(bank):.2f}  --  Take Home: {bank[-1]-bank_amount:.2f}"
            plt.plot(bank, marker='o', linestyle='-', label=f"{p_name}'s Bank History")
            plt.plot([bank_amount]*len(bank), marker='', linestyle='-', color='black', label=f"Initial Bank")
            plt.legend()
            plt.title(plot_label)
            plt.xlabel("Spin Number")
            plt.ylabel("Bank Amount")
            plt.show()

            # update the roulette fields
            self.roulette_final_bank_value.config(text=f"{player.running_bank[-1]:.2f}")
            self.roulette_max_bank_value.config(text=f"{max(player.running_bank):.2f}")
            self.roulette_min_bank_value.config(text=f"{min(player.running_bank):.2f}")


        except Exception as ex:
            self.game_messages.replace("1.0", tk.END, f"Error Placing Bet: {ex}")
            return # -------------------------------------------------------------------------------------------------->




    # -------------------------------------------------------------------------------------
    #                                  Poker
    # -------------------------------------------------------------------------------------


    def update_pot_and_current_bet_display(self):
        self.pot.config(text=f"Pot: {self.casino.poker_table.pot}")
        self.current_bet.config(text=f"Current Bet: {self.casino.poker_table.current_table_bet}")
        self.poker_game_state.config(text=f"Game State: {self.casino.poker_table.game_state.name}")

    def start_poker(self):
        table = self.casino.poker_table # type: poker.PokerTable
        game_number = table.get_game_number()
        if game_number == 0:
            ai_players = [poker.AiPokerPlayer("Bjort"),
                          poker.AiPokerPlayer("Cromulen"),
                          poker.AiPokerPlayer("Dorp"),
                          poker.AiPokerPlayer("Fluub"),
                          poker.AiPokerPlayer("HmOo"),]
            human_player = [poker.PokerPlayer("Humon")]
            self.casino.poker_table.new_game(poker.PokerGames.OMAHA, 2, ai_players, human_player )
        else:
            table.next_game()
        # print game state to the game messages text field
        self.game_messages.replace("1.0", tk.END, self.casino.poker_table.get_game_state_string())
        self.update_pot_and_current_bet_display()

    def button_bet(self):
        amount = self.bet_amount.get()
        table = self.casino.poker_table
        try:
            table.human_bet(int(amount))
        except Exception as ex:
            self.game_messages.replace("1.0", tk.END, f'Invalid Bet: {ex}')
        else:
            table.progress_game('button_bet')
            self.update_pot_and_current_bet_display()
            # replace game message with updated message
            self.game_messages.replace("1.0", tk.END, table.get_game_state_string())

    def button_check(self):
        amount = 0
        table = self.casino.poker_table
        try:
            table.human_bet(int(amount))
        except Exception as ex:
            self.game_messages.replace("1.0", tk.END, f'Invalid Bet: {ex}')
        else:
            table.progress_game('button_bet')
            self.update_pot_and_current_bet_display()
            # replace game message with updated message
            self.game_messages.replace("1.0", tk.END, table.get_game_state_string())

    def button_fold(self):
        for human in self.casino.poker_table.human_players: # type: poker.PokerPlayer # at this point there is only 1 human player but it's a list
            human.folded = True
        self.casino.poker_table.progress_game('button_bet')
        self.update_pot_and_current_bet_display()
        # replace game message with updated message
        self.game_messages.replace("1.0", tk.END, self.casino.poker_table.get_game_state_string())



