from functools import lru_cache

class Connect4:
    def __init__(self):
        # Initialize a 6-row by 7-column board using a 2D list
        self.rows = 6
        self.cols = 7
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
    
    def get_board_state(self):
        return self.board

    def check_move_color(self):
        # Determine turn based on the piece count; 1 if even (Red), -1 if odd (Yellow)
        piece_count = sum(1 for row in self.board for cell in row if cell != 0)
        return 1 if piece_count % 2 == 0 else -1

    def get_valid_moves(self, board=None):
        board = self.board if board is None else board
        # Valid moves are columns where the top cell is empty
        valid_columns = [col for col in range(self.cols) if board[0][col] == 0]
        return valid_columns

    def apply_move(self, board, col, color):
        # Place the piece in the lowest available row in the selected column
        for row in reversed(range(self.rows)):
            if board[row][col] == 0:
                board[row][col] = color
                return row, col  # Return the position where the piece was placed
        return None  # The column is full; should not happen if checked before

    def check_winner(self, board, color, row, col):
        # Check all directions from the last move for a winning sequence
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Horizontal, vertical, two diagonals
        for dr, dc in directions:
            count = 1  # Include the last move itself
            for dir in [1, -1]:  # Check both positive and negative directions
                r, c = row, col
                while True:
                    r += dr * dir
                    c += dc * dir
                    if 0 <= r < self.rows and 0 <= c < self.cols and board[r][c] == color:
                        count += 1
                        if count >= 4:
                            return True
                    else:
                        break
        return False

    def is_full(self, board=None):
        board = self.board if board is None else board
        # The board is full if there are no empty cells in the top row
        return all(cell != 0 for cell in board[0])

    def get_game_result(self, board, color, row, col):
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
    def get_game_result_after_last_move(self, board, last_color):
        # Check for a winner after the last move
        for row in range(self.rows):
            for col in range(self.cols):
                if board[row][col] == last_color:
                    if self.check_winner(board, last_color, row, col):
                        return "red_win" if last_color == 1 else "yellow_win"
        if self.is_full(board):
            return "tie"
        return "undecided"

    def evaluate_move_statistics(self, depth=4):
        """
        Evaluate the statistics for each possible move.
        :param depth: int - The depth to explore moves.
        :return: dict - Statistics for each move column.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves(self.board)
        move_statistics = {}
        self.memo = {}  # Reset memoization cache

        for col in valid_moves:
            # Create a copy of the board and apply the move
            new_board = [row[:] for row in self.board]
            row, col_pos = self.apply_move(new_board, col, color)
            # Get statistics for this move
            stats = self.simulate_move_tree_statistics(new_board, depth - 1, -color)
            # Normalize statistics percentages
            total = sum(stats.values())
            percentages = {key: (stats.get(key, 0) / total) * 100 if total > 0 else 0 for key in ['red_win', 'yellow_win', 'tie', 'undecided']}
            move_statistics[col] = {
                'percentages': percentages,
            }
        return move_statistics

    def simulate_move_tree_statistics(self, board, depth, current_color):
        result = self.get_game_result_after_last_move(board, -current_color)
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
            new_board = [row[:] for row in board]
            row, col_pos = self.apply_move(new_board, col, current_color)
            immediate_result = self.get_game_result(new_board, current_color, row, col_pos)
            if immediate_result != "undecided":
                outcome = {immediate_result: 1}
            else:
                outcome = self.simulate_move_tree_statistics(new_board, depth - 1, -current_color)
            # Aggregate results
            for key in results:
                results[key] += outcome.get(key, 0)
        self.memo[key] = results
        return results
    def get_move_evaluations(self, depth=4):
        """
        Evaluate all valid moves and return their evaluations.
        :param depth: int - The depth to explore moves.
        :return: dict - Evaluations for each valid move.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves(self.board)
        move_evaluations = {}
        self.memo = {}  # Reset memoization cache

        for col in valid_moves:
            new_board = [row[:] for row in self.board]
            row, col_pos = self.apply_move(new_board, col, color)
            result = self.get_game_result(new_board, color, row, col_pos)
            if result == "red_win":
                eval = 1
            elif result == "yellow_win":
                eval = -1
            elif result == "tie":
                eval = 0
            else:
                eval = self.simulate_move_tree(tuple(map(tuple, new_board)), depth - 1, -color, -float('inf'), float('inf'))
            move_evaluations[col] = eval

        return move_evaluations

    def __str__(self):
        color_map = {0: ' . ', 1: ' R ', -1: ' Y '}
        string = ''
        for row in self.board:
            string += '|' + ''.join([color_map[cell] for cell in row]) + '|\n'
        string += '  ' + '  '.join(map(str, range(self.cols))) + '\n'
        return string
