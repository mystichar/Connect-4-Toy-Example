import string
import curses
from connect4 import Connect4

class Connect4Game:
    def __init__(self):
        self.game = Connect4()
        self.column_letters = string.ascii_uppercase[:7]  # Limit to 7 columns for Connect 4
        self.current_player_color = 1  # Red starts

    def setup_colors(self, stdscr):
        # Initialize color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)   # Red color for player 1
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow color for player -1

    def display_board(self, stdscr):
        stdscr.clear()
        stdscr.addstr("Current board:\n")

        # Display the board using `curses` colors
        max_row = max(row for row, _ in self.game.board.keys())
        max_col = max(col for _, col in self.game.board.keys())
        for row in range(max_row, -1, -1):
            stdscr.addstr("|")
            for col in range(max_col + 1):
                cell = self.game.board.get((row, col), 0)
                if cell == 1:  # Red piece
                    stdscr.addstr("0", curses.color_pair(1))
                elif cell == -1:  # Yellow piece
                    stdscr.addstr("0", curses.color_pair(2))
                else:  # Empty cell
                    stdscr.addstr(" ")
                stdscr.addstr("|")
            stdscr.addstr("\n")
        stdscr.refresh()

    def display_available_moves(self, stdscr):
        moves = self.game.get_valid_moves(self.current_player_color)
        
        stdscr.addstr("Available moves:\n")
        move_options = []
        for i, state in enumerate(moves):
            col_letter = self.column_letters[i]
            move_options.append((col_letter, state))
            stdscr.addstr(f"{col_letter}: Column {i}\n")

        return move_options

    def select_move(self, stdscr, move_options):
        idx = 0
        while True:
            # Display the potential board for the currently selected move
            self.game.board = move_options[idx][1]
            self.display_board(stdscr)
            stdscr.addstr(f"Use arrow keys to navigate and press Enter to select a move.\n")
            stdscr.addstr(f"Selected move: {move_options[idx][0]}\n")
            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_LEFT and idx > 0:
                idx -= 1
            elif key == curses.KEY_RIGHT and idx < len(move_options) - 1:
                idx += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
                return move_options[idx][1]  # Return the selected board state

    def switch_player(self):
        self.current_player_color *= -1

    def check_for_winner(self, stdscr):
        if self.game.check_winner(self.current_player_color):
            color_name = "Red" if self.current_player_color == 1 else "Yellow"
            stdscr.addstr(f"{color_name} wins!\n")
            stdscr.refresh()
            stdscr.getch()  # Wait for key press before exiting
            return True
        return False

    def play(self, stdscr):
        curses.curs_set(0)  # Hide the cursor
        self.setup_colors(stdscr)
        stdscr.clear()
        stdscr.addstr("Welcome to Connect 4!\n")
        self.display_board(stdscr)

        while True:
            move_options = self.display_available_moves(stdscr)
            if not move_options:
                stdscr.addstr("It's a draw! No more moves available.\n")
                stdscr.refresh()
                stdscr.getch()  # Wait for key press before exiting
                break

            new_board_state = self.select_move(stdscr, move_options)
            self.game.board = new_board_state
            self.display_board(stdscr)

            if self.check_for_winner(stdscr):
                break

            self.switch_player()

# To play the game, run:
if __name__ == "__main__":
    curses.wrapper(Connect4Game().play)
