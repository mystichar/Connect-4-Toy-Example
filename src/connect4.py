# connect4.py

import cupy as cp
import numpy as np

class Connect4:
    def __init__(self):
        self.rows = 6
        self.cols = 7
        self.board = cp.zeros((self.rows, self.cols), dtype=cp.int32)
        
    def get_board_state(self):
        return self.board
    
    def check_move_color(self):
        piece_count = cp.count_nonzero(self.board)
        return 1 if piece_count % 2 == 0 else -1
    
    def get_valid_moves(self, board=None):
        board = self.board if board is None else board
        valid_columns = [col for col in range(self.cols) if board[0, col] == 0]
        return valid_columns
    
    def apply_move(self, board, col, color):
        for row in reversed(range(self.rows)):
            if board[row, col] == 0:
                board[row, col] = color
                return row, col
        return None
    
    def check_winner(self, board, color, row, col):
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal /
            (1, -1)   # Diagonal \
        ]
        
        for dr, dc in directions:
            count = 1
            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r += dr
                c += dc
            # Negative direction
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
        return cp.all(board[0, :] != 0)
    
    def get_game_result(self, board, color, row, col):
        if self.check_winner(board, color, row, col):
            return 1 if color == 1 else -1  # 1 for Red win, -1 for Yellow win
        elif self.is_full(board):
            return 0  # Tie
        else:
            return None  # Game continues
        
    def monte_carlo_simulation(self, num_simulations=10000, batch_size=512):
        color = self.check_move_color()
        valid_moves = self.get_valid_moves()
        win_counts = cp.zeros(len(valid_moves), dtype=cp.int32)
        
        # Calculate number of batches needed
        simulations_per_move = num_simulations // len(valid_moves)
        num_batches = (simulations_per_move + batch_size - 1) // batch_size  # Rounds up
        
        for idx, col in enumerate(valid_moves):
            batch_wins = 0
            for batch in range(num_batches):
                current_batch_size = min(batch_size, simulations_per_move - batch * batch_size)
                batch_wins += self.simulate_games(col, color, current_batch_size)
            win_counts[idx] = batch_wins
        
        # Transfer results to CPU and compute win rates
        win_counts_cpu = win_counts.get()
        win_rates = win_counts_cpu / simulations_per_move * 100  # Percentage
        move_statistics = {col: {'win_rate': float(win_rates[i])} for i, col in enumerate(valid_moves)}
        return move_statistics

    def simulate_games(self, col, color, num_simulations):
        """
        Simulate games in parallel using CuPy.
        :param col: The column to make the move.
        :param color: The color of the player making the move.
        :param num_simulations: Number of simulations to run.
        :return: Number of wins for the player.
        """
        # Initialize boards for simulations
        boards = cp.tile(self.board, (num_simulations, 1, 1))
        rows = cp.zeros(num_simulations, dtype=cp.int32)
        cols = cp.full(num_simulations, col, dtype=cp.int32)
        colors = cp.full(num_simulations, color, dtype=cp.int32)
        results = cp.zeros(num_simulations, dtype=cp.int32)  # 1: win, 0: loss or tie
        
        # Apply the initial move
        for i in range(num_simulations):
            row, _ = self.apply_move(boards[i], col, color)
            rows[i] = cp.int32(row)
        
        # Simulate the rest of the game
        simulate_games_kernel(
            boards,
            rows,
            cols,
            colors,
            results,
            self.rows,   # Pass as integer
            self.cols    # Pass as integer
        )
        
        # Count the number of wins
        wins = cp.count_nonzero(results == 1)
        return int(wins.get())
    
def simulate_games_kernel(boards, rows, cols, colors, results, rows_count, cols_count):
    num_simulations = boards.shape[0]
    for i in range(num_simulations):
        board = boards[i]
        color = int(colors[i])
        game_over = False
        while not game_over:
            # Switch player
            color = -color
            valid_moves = [col for col in range(cols_count) if board[0, col] == 0]
            if not valid_moves:
                break  # Tie
            move_col = cp.random.choice(valid_moves, size=1)[0]
            move_col = int(move_col)  # Convert to Python integer
            row, col = apply_move_gpu(board, move_col, color, rows_count, cols_count)
            if row == -1:
                break  # Invalid move, should not happen
            if check_winner_gpu(board, color, row, col, rows_count, cols_count):
                if color == int(colors[i]):
                    results[i] = 1  # Win
                else:
                    results[i] = 0  # Loss
                game_over = True

# Custom CUDA kernel for apply_move_gpu
apply_move_kernel = cp.RawKernel(r'''
extern "C" __global__
void apply_move(const int* board_in, int* board_out, int col, int color, int rows_count, int cols_count, int* result) {
    // Flattened board is used
    for (int row = rows_count - 1; row >= 0; --row) {
        int index = row * cols_count + col;
        if (board_in[index] == 0) {
            // Copy board_in to board_out
            for (int i = 0; i < rows_count * cols_count; ++i) {
                board_out[i] = board_in[i];
            }
            board_out[index] = color;
            result[0] = row;  // Store the row where the piece was placed
            result[1] = col;  // Store the column for consistency
            return;
        }
    }
    result[0] = -1;  // No empty row found
    result[1] = -1;  // No valid column found
}
''', 'apply_move')

def apply_move_gpu(board, col, color, rows_count, cols_count):
    # Prepare inputs for the kernel
    result = cp.zeros(2, dtype=cp.int32)  # Array to store row, col result
    # Flatten the board to 1D to use with raw kernel
    board_flat = board.ravel()
    board_flat_in = board_flat.copy()
    board_flat_out = cp.empty_like(board_flat)
    
    # Ensure scalar arguments are Python integers
    col = int(col)
    color = int(color)
    rows_count = int(rows_count)
    cols_count = int(cols_count)
    
    # Launch the kernel with 1 block and 1 thread
    apply_move_kernel(
        (1,), (1,),
        (board_flat_in, board_flat_out, col, color, rows_count, cols_count, result)
    )
    
    # Reshape board back to original shape
    board[...] = board_flat_out.reshape(rows_count, cols_count)
    # Copy result from GPU to CPU
    result_host = result.get()
    return int(result_host[0]), int(result_host[1])  # Return row and column as Python ints

def check_winner_gpu(board, color, row, col, rows_count, cols_count):
    directions = [
        (0, 1),
        (1, 0),
        (1, 1),
        (1, -1)
    ]
    for dr, dc in directions:
        count = 1
        # Positive direction
        r = row + dr
        c = col + dc
        while 0 <= r < rows_count and 0 <= c < cols_count and board[r, c] == color:
            count += 1
            if count >= 4:
                return True
            r += dr
            c += dc
        # Negative direction
        r = row - dr
        c = col - dc
        while 0 <= r < rows_count and 0 <= c < cols_count and board[r, c] == color:
            count += 1
            if count >= 4:
                return True
            r -= dr
            c -= dc
    return False
