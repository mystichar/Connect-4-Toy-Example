# connect4.py
from typing import Dict, Tuple

class Connect4:
    def __init__(self, efficiency=True):
        # Initialize a 5-tall by 7-wide empty board
        self.board = {(row, col): 0 for row in range(5) for col in range(7)}

    def get_board_state(self):
        return self.board

    def check_move_color(self):
        # Determine turn based on piece count; default to 1 if even, else -1
        piece_count = sum(1 for cell in self.board.values() if cell != 0)
        return 1 if piece_count % 2 == 0 else -1

    def get_valid_moves(self, board=None):
        board = self.board if not board else board
        max_row = max(row for row, _ in board.keys())
        max_col = max(col for _, col in board.keys())
        valid_columns = []

        for col in range(max_col + 1):
            for row in range(max_row + 1):
                cell = board.get((row, col), None)
                if cell == 0:
                    above_cell = board.get((row + 1, col), None)
                    if above_cell is not None or row == max_row:
                        valid_columns.append(col)
                    break
                elif cell is None:
                    break

        return valid_columns

    def __str__(self) -> str:
        color_map = {
            0: " |",
            1: "R|",   # Represent player 1 with 'R'
            -1: "Y|"   # Represent player -1 with 'Y'
        }

        max_row = max(row for row, _ in self.board.keys())
        max_col = max(col for _, col in self.board.keys())

        string = ""
        for row in range(max_row, -1, -1):
            string += "|"
            for col in range(max_col + 1):
                cell = self.board.get((row, col), None)
                string += color_map[cell] if cell is not None else " |"
            string += "\n"

        return string

    def check_winner(self, color=None, board=None):
        if color is None:
            color = -1 * self.check_move_color()

        if board is None:
            board = self.board  # Use the main game board if no specific board is provided

        max_row = max(row for row, _ in board.keys())
        max_col = max(col for _, col in board.keys())

        # Directions: vertical, horizontal, diagonal down-right, diagonal down-left
        directions = [
            (1, 0),  # Vertical
            (0, 1),  # Horizontal
            (1, 1),  # Diagonal down-right
            (1, -1)  # Diagonal down-left
        ]

        for row in range(max_row + 1):
            for col in range(max_col + 1):
                if board.get((row, col)) == color:
                    for dr, dc in directions:
                        if self._check_four_in_a_row(row, col, dr, dc, color, max_row, max_col, board):
                            return True
        return False

    def _check_four_in_a_row(self, row, col, dr, dc, color, max_row, max_col, board=None):
        board = self.board if not board else board
        # Check boundaries and four consecutive pieces in the given direction
        for i in range(4):
            new_row = row + i * dr
            new_col = col + i * dc
            if new_row > max_row or new_row < 0 or new_col > max_col or new_col < 0:
                return False
            if board.get((new_row, new_col)) != color:
                return False
        return True

    def get_game_result(self, board=None):
        board = self.board if not board else board
        if self.check_winner(1, board=board):
            return "red_win"
        elif self.check_winner(-1, board=board):
            return "yellow_win"
        elif self.is_full(board):
            return "tie"
        else:
            return "undecided"

    def apply_gravity(self):
        # Find unique columns in the board data
        columns = {col for row, col in self.board.keys()}
        for col in columns:
            # Collect all cells in the column, ordered from top to bottom
            col_cells = sorted([row for row, c in self.board.keys() if c == col], reverse=True)
            next_available_row = None

            for row in col_cells:
                cell_value = self.board.get((row, col), None)

                # If we encounter None, reset next available row (stop falling here)
                if cell_value is None:
                    next_available_row = None

                elif cell_value == 0:
                    # If it's an empty cell, set it as the next available row if none is set
                    if next_available_row is None:
                        next_available_row = row

                elif cell_value in (-1, 1):
                    # If there's a piece and we have an available row, move the piece down
                    if next_available_row is not None and next_available_row != row:
                        self.board[(next_available_row, col)] = cell_value
                        self.board[(row, col)] = 0
                        next_available_row -= 1  # Update next available position for further pieces
                    else:
                        # Set the next available row as one above the current piece
                        next_available_row = row - 1

    def evaluate_move_statistics(self, depth=4, smart_players=False):
        """
        Evaluate the statistics for each possible move.
        :param depth: int - The depth to explore moves.
        :param smart_players: bool - If true, stops exploration when a winning move is found.
        :return: dict - Statistics for each move column.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves(self.board)
        move_statistics = {}

        for col in valid_moves:
            # Create a copy of the board and apply the move
            board_copy = self.board.copy()
            self.apply_move(board_copy, col, color)

            # Get statistics and move tree for this column
            stats, move_tree = self.simulate_move_tree(board_copy, depth - 1, -color, smart_players=smart_players)
            
            # Normalize statistics percentages
            total = sum(stats.values())
            percentages = {key: (stats.get(key, 0) / total) * 100 for key in ['red_win', 'yellow_win', 'tie', 'undecided']}
            move_statistics[col] = {
                'percentages': percentages,
                'move_tree': move_tree  # Attach the move tree for debugging or further analysis
            }

        return move_statistics

    def simulate_move_tree(self, board, depth, current_color, smart_players=False):
        result = self.get_game_result(board)
        node = {
            'board': board.copy(),
            'result': result,
            'children': []
        }

        if result != "undecided" or depth == 0:
            # Return the result and the node with no children
            return ({result: 1}, node)

        moves = self.get_valid_moves(board)
        if not moves:
            return ({"tie": 1}, node)

        results = {"red_win": 0, "yellow_win": 0, "tie": 0, "undecided": 0}
        next_color = -current_color

        for col in moves:
            new_board = board.copy()
            self.apply_move(new_board, col, current_color)

            immediate_result = self.get_game_result(new_board)

            if smart_players and immediate_result != "undecided":
                # Immediate result detected
                outcome = {immediate_result: 1}
                child_node = {
                    'move': col,
                    'board': new_board.copy(),
                    'result': immediate_result,
                    'children': []
                }
            else:
                # Continue exploring
                outcome, child_node = self.simulate_move_tree(
                    new_board, depth - 1, next_color, smart_players)

                child_node['move'] = col

            # Aggregate results
            for key in results:
                results[key] += outcome.get(key, 0)

            node['children'].append(child_node)

        return (results, node)
    
    def apply_move(self, board, col, color):
        # Apply the move to a given board (copy) without altering the original board.
        max_row = max(row for row, _ in board.keys())
        for row in range(max_row + 1):
            if board.get((row, col), 0) == 0:
                board[(row, col)] = color
                return
        # If the column is full, do nothing

    def is_full(self, board=None):
        board = self.board if not board else board
        return all(cell != 0 for cell in board.values() if cell is not None)

