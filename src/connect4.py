import torch

# Define the device based on GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Connect4:
    def __init__(self):
        self.rows = 6
        self.cols = 7
        # Initialize the board as a 2D tensor on the specified device
        self.board = torch.zeros((self.rows, self.cols), dtype=torch.int8, device=device)
    
    def get_board_state(self):
        return self.board
    
    def check_move_color(self):
        # Determine turn based on the piece count; 1 if even (Red), -1 if odd (Yellow)
        piece_count = (self.board != 0).sum().item()
        return 1 if piece_count % 2 == 0 else -1
    
    def get_valid_moves(self, board):
        # Valid moves are columns where the top cell is empty
        valid_columns = (board[0, :] == 0).nonzero(as_tuple=True)[0].tolist()
        return valid_columns
    
    def apply_move(self, board, col, color):
        # Place the piece in the lowest available row in the selected column
        for row in reversed(range(self.rows)):
            if board[row, col] == 0:
                board[row, col] = color
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
                    if 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                        count += 1
                        if count >= 4:
                            return True
                    else:
                        break
        return False
    
    def is_full(self, board):
        # The board is full if there are no empty cells in the top row
        return (board[0, :] != 0).all().item()
    
    def get_game_result_single(self, board, last_color):
        # Check for a winner after the last move
        for row in range(self.rows):
            for col in range(self.cols):
                if board[row, col] == last_color:
                    if self.check_winner(board, last_color, row, col):
                        return "red_win" if last_color == 1 else "yellow_win"
        if self.is_full(board):
            return "tie"
        return "undecided"
       
    def get_game_results_after_last_move(self, boards, last_color):
        """
        Check for a winner after the last move for a batch of boards.
        :param boards: Tensor of shape (batch_size, rows, cols)
        :param last_color: int - The color of the last move.
        :return: Tensor of game results for each board.
        """
        batch_size = boards.shape[0]
        results = []
        for i in range(batch_size):
            board = boards[i]
            result = self.get_game_result_single(board, last_color)
            results.append(result)
        return results  # List of results for each board
    
    def simulate_move_tree_statistics(self, boards, depth, current_color):
        """
        Simulate move tree statistics using batch processing.
        :param boards: Tensor of shape (batch_size, rows, cols)
        :param depth: int - Remaining depth to explore.
        :param current_color: int - Current player's color.
        :return: dict - Aggregated statistics.
        """
        results = {'red_win': 0, 'yellow_win': 0, 'tie': 0, 'undecided': 0}
        batch_size = boards.shape[0]
    
        if depth == 0 or batch_size == 0:
            results['undecided'] += batch_size
            return results
    
        # Check for game over in all boards
        game_results = self.get_game_results_after_last_move(boards, -current_color)
    
        # Count results
        for result in ['red_win', 'yellow_win', 'tie']:
            count = game_results.count(result)
            results[result] += count
    
        # Filter boards that are not yet decided
        undecided_indices = [i for i, res in enumerate(game_results) if res == 'undecided']
        if not undecided_indices:
            return results
    
        # Prepare next batch of boards
        undecided_boards = boards[undecided_indices]
        next_boards = []
    
        # For each undecided board, generate all valid moves
        for board in undecided_boards:
            valid_moves = self.get_valid_moves(board)
            for col in valid_moves:
                new_board = board.clone()
                self.apply_move(new_board, col, current_color)
                next_boards.append(new_board)
    
        if not next_boards:
            results['tie'] += len(undecided_boards)
            return results
    
        # Stack the next batch of boards
        next_boards = torch.stack(next_boards)
    
        # Recurse with the next batch
        next_results = self.simulate_move_tree_statistics(next_boards, depth - 1, -current_color)
    
        # Aggregate results
        for key in results:
            results[key] += next_results.get(key, 0)
    
        return results
    
    def evaluate_move_statistics(self, depth=4):
        """
        Evaluate the statistics for each possible move.
        :param depth: int - The depth to explore moves.
        :return: dict - Statistics for each move column.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves(self.board)
        move_statistics = {}
    
        # Create a batch of boards for all valid moves
        boards = []
        for col in valid_moves:
            new_board = self.board.clone()
            self.apply_move(new_board, col, color)
            boards.append(new_board)
    
        if not boards:
            return move_statistics
    
        # Stack the boards into a tensor
        boards = torch.stack(boards)
    
        # Simulate move tree statistics on the batch
        stats = self.simulate_move_tree_statistics(boards, depth - 1, -color)
    
        # Process statistics for each move
        total = sum(stats.values())
        percentages = {key: (stats.get(key, 0) / total) * 100 if total > 0 else 0 for key in ['red_win', 'yellow_win', 'tie', 'undecided']}
    
        for idx, col in enumerate(valid_moves):
            move_statistics[col] = {
                'percentages': percentages,
            }
    
        return move_statistics
