import string
from connect4 import Connect4

class Connect4Game:
    def __init__(self):
        self.game = Connect4()
        self.column_letters = string.ascii_uppercase[:7]  # Limit to 7 columns for Connect 4
        self.current_player_color = 1  # Red starts

    def display_board(self):
        print("\nCurrent board:")
        print(self.game)

    def display_available_moves(self):
        # Get the current player's color
        moves = self.game.get_valid_moves(self.current_player_color)
        
        print("\nAvailable moves:")
        move_options = {}
        for i, state in enumerate(moves):
            col_letter = self.column_letters[i]
            print(f"\nOption {col_letter}:")
            
            # Temporarily set the board to the state to display it
            original_board = self.game.board.copy()
            self.game.board = state  # Set board to this potential state
            print(self.game)  # Print this potential board state
            self.game.board = original_board  # Restore original board
            
            move_options[col_letter] = state  # Map letters to board states
        return move_options

    def switch_player(self):
        # Switch the player color
        self.current_player_color *= -1

    def check_for_winner(self):
        # Check if the current player has won
        if self.game.check_winner(self.current_player_color):
            color_name = "Red" if self.current_player_color == 1 else "Yellow"
            print(f"{color_name} wins!")
            return True
        return False

    def play(self):
        print("Welcome to Connect 4!")
        self.display_board()

        while True:
            # Display available moves
            move_options = self.display_available_moves()
            if not move_options:
                print("It's a draw! No more moves available.")
                break

            # Ask for user input
            player_name = "Red" if self.current_player_color == 1 else "Yellow"
            move = input(f"{player_name}, choose your move by entering a letter: ").upper()

            if move in move_options:
                # Update the board with the chosen move
                self.game.board = move_options[move]
                self.display_board()

                # Check if the current player has won
                if self.check_for_winner():
                    break

                # Switch player for the next turn
                self.switch_player()
            else:
                print("Invalid move. Please choose a valid option.")

# To play the game, run:
if __name__ == "__main__":
    game = Connect4Game()
    game.play()
