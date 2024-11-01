import numpy as np
from scipy.signal import convolve2d

class Connect4:
    def __init__(self):
        # Initialize a 6-row by 7-column board using NumPy arrays
        self.rows = 6
        self.cols = 7
        self.board = np.zeros((self.rows, self.cols), dtype=int)

    def get_board_state(self):
        return self.board

    def check_move_color(self):
        # Determine turn based on the piece count; 1 if even (Red), -1 if odd (Yellow)
        piece_count = np.count_nonzero(self.board)
        return 1 if piece_count % 2 == 0 else -1

    def get_valid_moves(self, board=None):
        board = self.board if board is None else board
        # Valid moves are columns where the top cell is empty
        valid_columns = [col for col in range(self.cols) if board[0, col] == 0]
        return valid_columns

    def apply_move(self, board, col, color):
        # Place the piece in the lowest available row in the selected column
        for row in reversed(range(self.rows)):
            if board[row, col] == 0:
                board[row, col] = color
                return row, col  # Return the position where the piece was placed
        return None  # The column is full; should not happen if checked before

    def check_winner(self, board, color, row, col):
        """
        Checks if the last move at (row, col) created a winning sequence for the given color.
        Only checks in the vicinity of the last move to optimize performance.
        """
        directions = [
            (0, 1),   # Horizontal (left-right)
            (1, 0),   # Vertical (up-down)
            (1, 1),   # Diagonal (top-left to bottom-right)
            (1, -1)   # Diagonal (top-right to bottom-left)
        ]
        
        for dr, dc in directions:
            count = 1  # Start with the last move itself

            # Check in the positive direction for this vector
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r += dr
                c += dc

            # Check in the negative direction for this vector
            r, c = row - dr, col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r -= dr
                c -= dc

        return False

    def is_full(self, board=None):
        board = self.board if board is None else board
        # The board is full if there are no empty cells in the top row
        return np.all(board[0, :] != 0)

    def get_game_result(self, board, color, row, col):
        """
        Check for a game result after the last move.
        :param board: 2D numpy array representing the game board.
        :param color: Integer representing the player's color (1 for Red, -1 for Yellow).
        :param row: Integer row index of the last move.
        :param col: Integer column index of the last move.
        """
        if self.check_winner(board, color, row, col):
            return "red_win" if color == 1 else "yellow_win"
        elif self.is_full(board):
            return "tie"
        else:
            return "undecided"

    def evaluate_result(self, result):
        # Assign numerical scores to game outcomes for the minimax algorithm
        if result == "red_win":
            return 1
        elif result == "yellow_win":
            return -1
        else:  # "tie" or "undecided"
            return 0

    def simulate_move_tree_statistics(self, board, depth, current_color, last_move=None):
        """
        Simulate moves recursively to gather statistics.
        :param board: 2D numpy array representing the game board.
        :param depth: The depth to explore moves.
        :param current_color: Integer representing the current player's color.
        :param last_move: Tuple (row, col) representing the last move played.
        :return: A dictionary with win, loss, tie, and undecided counts.
        """
        if last_move is not None:
            row, col = last_move
            result = self.get_game_result(board, -current_color, row, col)
        else:
            result = "undecided"

        if result != "undecided" or depth == 0:
            return {result: 1}
        
        board_tuple = tuple(map(tuple, board))
        key = (board_tuple, current_color, depth)
        if key in self.memo:
            return self.memo[key]
        
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return {"tie": 1}
        
        results = {"red_win": 0, "yellow_win": 0, "tie": 0, "undecided": 0}
        for col in valid_moves:
            new_board = board.copy()
            row, col_pos = self.apply_move(new_board, col, current_color)
            immediate_result = self.get_game_result(new_board, current_color, row, col_pos)
            if immediate_result != "undecided":
                outcome = {immediate_result: 1}
            else:
                outcome = self.simulate_move_tree_statistics(new_board, depth - 1, -current_color, (row, col_pos))
            
            # Aggregate results
            for key in results:
                results[key] += outcome.get(key, 0)
        
        self.memo[key] = results
        return results

    def evaluate_move_statistics(self, depth=4):
        """
        Evaluate the statistics for each possible move.
        :param depth: int - The depth to explore moves.
        :return: dict - Statistics for each move column.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves()
        move_statistics = {}
        self.memo = {}  # Reset memoization cache

        for col in valid_moves:
            new_board = self.board.copy()
            row, col_pos = self.apply_move(new_board, col, color)
            stats = self.simulate_move_tree_statistics(new_board, depth - 1, -color, (row, col_pos))
            total = sum(stats.values())
            percentages = {key: (stats.get(key, 0) / total) * 100 if total > 0 else 0
                           for key in ['red_win', 'yellow_win', 'tie', 'undecided']}
            move_statistics[col] = {
                'percentages': percentages,
            }

        return move_statistics

    def __str__(self):
        color_map = {0: ' . ', 1: ' R ', -1: ' Y '}
        string = ''
        for row in self.board:
            string += '|' + ''.join([color_map[cell] for cell in row]) + '|\n'
        string += '  ' + '  '.join(map(str, range(self.cols))) + '\n'
        return string
