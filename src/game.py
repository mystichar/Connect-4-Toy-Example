import string
import curses
from connect4 import Connect4

class Connect4Game:
    def __init__(self, depth=4):
        self.game = Connect4()
        self.depth = depth
        self.column_letters = string.ascii_uppercase[:7]  # Limit to 7 columns for Connect 4
        self.current_player_color = 1  # Red starts

    def setup_colors(self, stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)   # Red color for player 1
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow color for player -1

    def prompt_recursion_depth(self, stdscr):
        stdscr.clear()
        stdscr.addstr("Enter recursion depth (default is 4): ")
        stdscr.refresh()
        curses.echo()
        depth_input = stdscr.getstr().decode("utf-8").strip()
        curses.noecho()
        self.depth = int(depth_input) if depth_input.isdigit() else 4

    def display_board(self, stdscr):
        stdscr.clear()
        stdscr.addstr("Current board:\n")

        max_row = max(row for row, _ in self.game.board.keys())
        max_col = max(col for _, col in self.game.board.keys())
        for row in range(max_row, -1, -1):
            stdscr.addstr("|")
            for col in range(max_col + 1):
                cell = self.game.board.get((row, col), 0)
                if cell == 1:
                    stdscr.addstr("0", curses.color_pair(1))
                elif cell == -1:
                    stdscr.addstr("0", curses.color_pair(2))
                else:
                    stdscr.addstr(" ")
                stdscr.addstr("|")
            stdscr.addstr("\n")
        stdscr.refresh()

    def display_available_moves(self, stdscr):
        move_statistics = self.game.evaluate_move_statistics(depth=self.depth, smart_players=True)
        stdscr.addstr("Available moves:\n")

        move_options = []
        for i, (col, stats) in enumerate(move_statistics.items()):
            col_letter = self.column_letters[col]
            move_options.append((col_letter, col, stats))

            red_win = stats['percentages']['red_win']
            yellow_win = stats['percentages']['yellow_win']
            tie = stats['percentages']['tie']
            undecided = stats['percentages']['undecided']

            stdscr.addstr(f"{col_letter}: Column {col} - ")
            stdscr.addstr(f"Red Win: {red_win:.1f}%, ")
            stdscr.addstr(f"Yellow Win: {yellow_win:.1f}%, ")
            stdscr.addstr(f"Tie: {tie:.1f}%, ")
            stdscr.addstr(f"Undecided: {undecided:.1f}%\n")

        return move_options

    def select_move(self, stdscr, move_options):
        idx = 0
        while True:
            col_letter, col, stats = move_options[idx]
            board_copy = self.game.board.copy()
            self.game.apply_move(board_copy, col, self.current_player_color)
            self.display_board(stdscr)
            
            stdscr.addstr(f"\nMove: {col_letter} - Column {col}\n")
            stdscr.addstr(f"Red Win: {stats['percentages']['red_win']:.1f}%\n")
            stdscr.addstr(f"Yellow Win: {stats['percentages']['yellow_win']:.1f}%\n")
            stdscr.addstr(f"Tie: {stats['percentages']['tie']:.1f}%\n")
            stdscr.addstr(f"Undecided: {stats['percentages']['undecided']:.1f}%\n")

            stdscr.addstr("\nUse arrow keys to navigate and press Enter to select.\n")
            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_LEFT and idx > 0:
                idx -= 1
            elif key == curses.KEY_RIGHT and idx < len(move_options) - 1:
                idx += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                return move_options[idx][1]  # Return the selected column

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
        curses.curs_set(0)
        self.setup_colors(stdscr)
        self.prompt_recursion_depth(stdscr)
        self.display_board(stdscr)

        while True:
            move_options = self.display_available_moves(stdscr)
            if not move_options:
                stdscr.addstr("It's a draw! No more moves available.\n")
                stdscr.refresh()
                stdscr.getch()
                break

            selected_column = self.select_move(stdscr, move_options)
            self.game.apply_move(self.game.board, selected_column, self.current_player_color)
            self.display_board(stdscr)

            if self.check_for_winner(stdscr):
                break

            self.switch_player()

if __name__ == "__main__":
    curses.wrapper(Connect4Game().play)
