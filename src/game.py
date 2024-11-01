import string
import curses
import time  # Import time for measuring execution duration
from connect4 import Connect4

class Connect4Game:
    def __init__(self, depth=4):
        self.game = Connect4()
        self.depth = depth
        self.column_letters = string.ascii_uppercase[:self.game.cols]  # Adjusted to match board columns
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
                cell = self.game.board[row][col]
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
        # Start timing the simulation
        start_time = time.time()
        
        move_statistics = self.game.evaluate_move_statistics(depth=self.depth)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        stdscr.addstr("Available moves:\n")
        stdscr.addstr(f"Simulation execution time: {execution_time:.2f} seconds\n")  # Display execution time
        stdscr.refresh()  # Ensure it refreshes immediately

        move_options = []
        for col, stats in move_statistics.items():
            col_letter = self.column_letters[col]
            move_options.append((col_letter, col, stats))

            percentages = stats['percentages']
            red_win = percentages['red_win']
            yellow_win = percentages['yellow_win']
            tie = percentages['tie']
            undecided = percentages['undecided']

            stdscr.addstr(f"{col_letter}: Column {col} - ")
            stdscr.addstr(f"Red Win: {red_win:.1f}%, ")
            stdscr.addstr(f"Yellow Win: {yellow_win:.1f}%, ")
            stdscr.addstr(f"Tie: {tie:.1f}%, ")
            stdscr.addstr(f"Undecided: {undecided:.1f}%\n")

        stdscr.refresh()  # Refresh at the end to show all output
        return move_options, execution_time  # Return execution_time


    def switch_player(self):
        self.current_player_color *= -1

    def check_for_winner(self, stdscr, row, col):
        result = self.game.get_game_result_single(self.game.board, self.current_player_color)
        if result == "red_win" or result == "yellow_win":
            color_name = "Red" if self.current_player_color == 1 else "Yellow"
            stdscr.addstr(f"{color_name} wins!\n")
            stdscr.refresh()
            stdscr.getch()  # Wait for key press before exiting
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
        self.display_board(stdscr)

        while True:
            move_options, execution_time = self.display_available_moves(stdscr)
            if not move_options:
                stdscr.addstr("It's a draw! No more moves available.\n")
                stdscr.refresh()
                stdscr.getch()
                break

            selected_column = self.select_move(stdscr, move_options, execution_time)
            row, col = self.game.apply_move(self.game.board, selected_column, self.current_player_color)
            self.display_board(stdscr)

            if self.check_for_winner(stdscr, row, col):
                break

            self.switch_player()
  
    def select_move(self, stdscr, move_options, execution_time):
        idx = 0  # Start with the first available move
        while True:
            col_letter, col, stats = move_options[idx]
            percentages = stats['percentages']
            # Create a copy of the board as a tensor and apply the move for visualization
            new_board = self.game.board.clone()  # Clone tensor to avoid modifying original
            row, col_pos = self.game.apply_move(new_board, col, self.current_player_color)
            
            # Display the board after the move
            stdscr.clear()
            stdscr.addstr(f"Simulating move: {col_letter} - Column {col}\n")
            for r in range(self.game.rows):
                stdscr.addstr("|")
                for c in range(self.game.cols):
                    cell = new_board[r, c]
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
            stdscr.addstr(f"Red Win: {percentages['red_win']:.1f}%\n")
            stdscr.addstr(f"Yellow Win: {percentages['yellow_win']:.1f}%\n")
            stdscr.addstr(f"Tie: {percentages['tie']:.1f}%\n")
            stdscr.addstr(f"Undecided: {percentages['undecided']:.1f}%\n")
            stdscr.addstr(f"Execution Time: {execution_time:.3f} seconds\n")
            stdscr.addstr("\nUse LEFT/RIGHT arrow keys to navigate and press ENTER to select.\n")
            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_LEFT and idx > 0:
                idx -= 1
            elif key == curses.KEY_RIGHT and idx < len(move_options) - 1:
                idx += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                return col  # Return the selected column
       

if __name__ == "__main__":
    curses.wrapper(Connect4Game().play)
