import string
import curses
import time
from connect4 import Connect4Graph  # Ensure the class name matches

class Connect4Game:
    def __init__(self, depth=4):
        self.game = Connect4Graph()
        self.depth = depth
        self.column_letters = string.ascii_uppercase[:self.game.cols]
        self.current_player_color = 1  # Red starts

    def setup_colors(self, stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)     # Red color for player 1
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
        for row in range(self.game.rows):
            stdscr.addstr("|")
            for col in range(self.game.cols):
                cell = self.game.graph.nodes[(row, col)]['state']  # Access cell state from the graph
                if cell == 1:
                    stdscr.addstr("0", curses.color_pair(1))
                elif cell == -1:
                    stdscr.addstr("0", curses.color_pair(2))
                else:
                    stdscr.addstr(" ")
                stdscr.addstr("|")
            stdscr.addstr("\n")
        # Display column letters for user reference
        stdscr.addstr(" " + " ".join(self.column_letters) + "\n")
        stdscr.refresh()

    def display_available_moves(self, stdscr):
        start_time = time.time()
        
        move_statistics = self.game.evaluate_move_statistics(depth=self.depth)
        
        execution_time = time.time() - start_time
        
        stdscr.addstr("Available moves:\n")
        stdscr.addstr(f"Simulation execution time: {execution_time:.2f} seconds\n")
        stdscr.refresh()

        move_options = []
        for col, stats in move_statistics.items():
            if stats is None:  # Skip None results
                continue

            col_letter = self.column_letters[col]
            move_options.append((col_letter, col, stats))

            percentages = stats.get('percentages', {})
            red_win = percentages.get('red_win', 0)
            yellow_win = percentages.get('yellow_win', 0)
            tie = percentages.get('tie', 0)
            undecided = percentages.get('undecided', 0)

            stdscr.addstr(f"{col_letter}: Column {col} - ")
            stdscr.addstr(f"Red Win: {red_win:.1f}%, ")
            stdscr.addstr(f"Yellow Win: {yellow_win:.1f}%, ")
            stdscr.addstr(f"Tie: {tie:.1f}%, ")
            stdscr.addstr(f"Undecided: {undecided:.1f}%\n")

        stdscr.refresh()
        return move_options, execution_time

    def select_move(self, stdscr, move_options, execution_time):
        idx = 0
        stdscr.keypad(True)  # Enable keypad mode

        while True:
            # Clear only once at the start of each iteration
            stdscr.clear()

            # Get the current column's information
            col_letter, col, stats = move_options[idx]
            percentages = stats.get('percentages', {})

            # Create a copy of the board and apply the move for visualization
            new_board = self.game.graph  # Try using the same instance without copying

            # Render information once per iteration
            stdscr.addstr(f"Simulation execution time: {execution_time:.2f} seconds\n")
            stdscr.addstr(f"Simulating move: {col_letter} - Column {col} (Selected Index: {idx})\n")

            # Display the simulated board without copying
            for r in range(self.game.rows):
                stdscr.addstr("|")
                for c in range(self.game.cols):
                    cell = new_board.nodes[(r, c)]['state']
                    if cell == 1:
                        stdscr.addstr("0", curses.color_pair(1))
                    elif cell == -1:
                        stdscr.addstr("0", curses.color_pair(2))
                    else:
                        stdscr.addstr(" ")
                    stdscr.addstr("|")
                stdscr.addstr("\n")
            stdscr.addstr(" " + " ".join(self.column_letters) + "\n")
            stdscr.addstr(f"\nMove: {col_letter} - Column {col}\n")
            stdscr.addstr(f"Red Win: {percentages.get('red_win', 0):.1f}%\n")
            stdscr.addstr(f"Yellow Win: {percentages.get('yellow_win', 0):.1f}%\n")
            stdscr.addstr(f"Tie: {percentages.get('tie', 0):.1f}%\n")
            stdscr.addstr(f"Undecided: {percentages.get('undecided', 0):.1f}%\n")
            stdscr.addstr("\nUse 'a' to move left, 'd' to move right, and press ENTER to select.\n")

            # Final refresh
            stdscr.refresh()

            # Capture user input and handle navigation
            key = stdscr.getch()
            if key == ord('a') and idx > 0:  # Move left
                idx -= 1
            elif key == ord('d') and idx < len(move_options) - 1:  # Move right
                idx += 1
            elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key
                return col  # Return the selected column

    def switch_player(self):
        self.current_player_color *= -1

    def check_for_winner(self, stdscr, row, col):
        result = self.game.get_game_result(self.game.graph, self.current_player_color, row, col)
        if result == "red_win" or result == "yellow_win":
            color_name = "Red" if self.current_player_color == 1 else "Yellow"
            stdscr.addstr(f"{color_name} wins!\n")
            stdscr.refresh()
            stdscr.getch()
            return True
        elif result == "tie":
            stdscr.addstr("It's a tie!\n")
            stdscr.refresh()
            stdscr.getch()
            return True
        return False
    def play(self, stdscr):
        curses.curs_set(0)
        self.setup_colors(stdscr)
        self.prompt_recursion_depth(stdscr)
        stdscr.keypad(True)  # Enable keypad mode
        self.display_board(stdscr)

        while True:
            move_options, execution_time = self.display_available_moves(stdscr)
            if not move_options:
                stdscr.addstr("It's a draw! No more moves available.\n")
                stdscr.refresh()
                stdscr.getch()
                break

            selected_column = self.select_move(stdscr, move_options, execution_time)
            
            # Attempt to apply the move and check if it's valid
            move = self.game.apply_move(self.game.graph, selected_column, self.current_player_color)
            if not move:
                stdscr.addstr("Column is full! Please select another column.\n")
                stdscr.refresh()
                continue  # Prompt player to choose another column

            self.display_board(stdscr)

            row, col = move
            if self.check_for_winner(stdscr, row, col):
                break

            self.switch_player()


if __name__ == "__main__":
    game_instance = Connect4Game()
    try:
        curses.wrapper(game_instance.play)
    finally:
        game_instance.game.cleanup()
