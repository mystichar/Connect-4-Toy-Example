import numpy as np
import pycuda.autoinit
import pycuda.driver as drv
from pycuda.compiler import SourceModule

class Connect4:
    def __init__(self):
        # Initialize board dimensions
        self.rows = 6
        self.cols = 7
        self.board = np.zeros((self.rows, self.cols), dtype=int)

        # Precompute the solution filters
        self.solution_filters = self.generate_solution_filters()

    def generate_solution_filters(self):
        """
        Generate the solution filters for horizontal, vertical, and diagonal wins.
        Each filter is a bitmask that represents a winning position.
        """
        filters = []

        # Horizontal filters
        for row in range(self.rows):
            for col in range(self.cols - 3):
                mask = np.zeros((self.rows, self.cols), dtype=int)
                mask[row, col:col+4] = 1
                filters.append(mask.flatten())

        # Vertical filters
        for row in range(self.rows - 3):
            for col in range(self.cols):
                mask = np.zeros((self.rows, self.cols), dtype=int)
                mask[row:row+4, col] = 1
                filters.append(mask.flatten())

        # Positive diagonal filters
        for row in range(self.rows - 3):
            for col in range(self.cols - 3):
                mask = np.zeros((self.rows, self.cols), dtype=int)
                for i in range(4):
                    mask[row + i, col + i] = 1
                filters.append(mask.flatten())

        # Negative diagonal filters
        for row in range(3, self.rows):
            for col in range(self.cols - 3):
                mask = np.zeros((self.rows, self.cols), dtype=int)
                for i in range(4):
                    mask[row - i, col + i] = 1
                filters.append(mask.flatten())

        return np.array(filters, dtype=np.int32)

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

    def is_full(self, board=None):
        board = self.board if board is None else board
        # The board is full if there are no empty cells in the top row
        return np.all(board[0, :] != 0)

    def check_winner(self, board, color, row, col):
        """
        Checks if the last move at (row, col) created a winning sequence for the given color.
        """
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Positive diagonal
            (1, -1)   # Negative diagonal
        ]

        for dr, dc in directions:
            count = 1  # Start with the last move itself

            # Check in the positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r += dr
                c += dc

            # Check in the negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r -= dr
                c -= dc

        return False

    def get_game_result(self, board, color, row, col):
        """
        Check for a game result after the last move.
        """
        if self.check_winner(board, color, row, col):
            return "red_win" if color == 1 else "yellow_win"
        elif self.is_full(board):
            return "tie"
        else:
            return "undecided"

    def evaluate_move_statistics(self, depth=2):
        """
        Evaluate the statistics for each possible move using GPU acceleration.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves()
        move_statistics = {}

        # Prepare data for GPU
        boards_to_evaluate = []
        colors_to_evaluate = []
        moves_sequence = []

        # Initial moves
        for col in valid_moves:
            new_board = self.board.copy()
            row, col_pos = self.apply_move(new_board, col, color)
            boards_to_evaluate.append(new_board.flatten())
            colors_to_evaluate.append(-color)
            moves_sequence.append([col])
            # Store the last move positions for result checking
            last_moves = [(row, col_pos)]

        # Perform recursive move generation up to the specified depth
        for d in range(1, depth):
            new_boards = []
            new_colors = []
            new_moves_sequence = []
            new_last_moves = []
            for idx, board_flat in enumerate(boards_to_evaluate):
                board = board_flat.reshape((self.rows, self.cols))
                current_color = colors_to_evaluate[idx]
                sequence = moves_sequence[idx]
                valid_moves = self.get_valid_moves(board)

                for col in valid_moves:
                    next_board = board.copy()
                    row, col_pos = self.apply_move(next_board, col, current_color)
                    new_boards.append(next_board.flatten())
                    new_colors.append(-current_color)
                    new_moves_sequence.append(sequence + [col])
                    new_last_moves.append((row, col_pos))

            boards_to_evaluate = new_boards
            colors_to_evaluate = new_colors
            moves_sequence = new_moves_sequence
            last_moves = new_last_moves

        if not boards_to_evaluate:
            return move_statistics  # No moves to evaluate

        num_boards = len(boards_to_evaluate)
        boards_array = np.array(boards_to_evaluate, dtype=np.int32)
        colors_array = np.array(colors_to_evaluate, dtype=np.int32)

        # Prepare solution filters
        solution_filters = self.solution_filters
        num_filters = solution_filters.shape[0]

        # Allocate GPU memory
        results_array = np.zeros(num_boards, dtype=np.int32)

        # Copy data to GPU
        boards_gpu = drv.mem_alloc(boards_array.nbytes)
        drv.memcpy_htod(boards_gpu, boards_array)

        filters_gpu = drv.mem_alloc(solution_filters.nbytes)
        drv.memcpy_htod(filters_gpu, solution_filters)

        results_gpu = drv.mem_alloc(results_array.nbytes)

        # Define the GPU kernel
        mod = SourceModule("""
    __global__ void evaluate_positions(int *boards, int *filters, int *results,
                                       int num_boards, int num_filters, int board_size) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= num_boards) return;

        int *board = &boards[idx * board_size];
        int result = 0;  // 0: undecided, 1: red win, -1: yellow win

        for (int f = 0; f < num_filters; f++) {
            int *filter = &filters[f * board_size];
            int match_red = 1;
            int match_yellow = 1;

            for (int i = 0; i < board_size; i++) {
                if (filter[i] == 1) {
                    if (board[i] != 1) {
                        match_red = 0;
                    }
                    if (board[i] != -1) {
                        match_yellow = 0;
                    }
                }
            }

            if (match_red) {
                result = 1;
                break;
            }
            if (match_yellow) {
                result = -1;
                break;
            }
        }

        results[idx] = result;
    }
    """)

        func = mod.get_function("evaluate_positions")
        block_size = 256
        grid_size = (num_boards + block_size - 1) // block_size

        func(
            boards_gpu,
            filters_gpu,
            results_gpu,
            np.int32(num_boards),
            np.int32(num_filters),
            np.int32(self.rows * self.cols),
            block=(block_size, 1, 1),
            grid=(grid_size, 1)
        )

        # Retrieve results from GPU
        drv.memcpy_dtoh(results_array, results_gpu)

        # Aggregate results based on the initial move
        move_results = {}
        for idx, sequence in enumerate(moves_sequence):
            initial_move = sequence[0]
            result = results_array[idx]
            if initial_move not in move_results:
                move_results[initial_move] = {'red_win': 0, 'yellow_win': 0, 'undecided': 0}

            if result == 1:
                move_results[initial_move]['red_win'] += 1
            elif result == -1:
                move_results[initial_move]['yellow_win'] += 1
            else:
                move_results[initial_move]['undecided'] += 1

        # Calculate percentages
        for col, stats in move_results.items():
            total = sum(stats.values())
            percentages = {key: (value / total) * 100 if total > 0 else 0 for key, value in stats.items()}
            # Add tie percentage as 0 since we don't calculate ties here
            percentages['tie'] = 0.0
            move_statistics[col] = {'percentages': percentages}

        return move_statistics

    def __str__(self):
        color_map = {0: ' . ', 1: ' R ', -1: ' Y '}
        string = ''
        for row in self.board:
            string += '|' + ''.join([color_map[cell] for cell in row]) + '|\n'
        string += '  ' + '  '.join(map(str, range(self.cols))) + '\n'
        return string
