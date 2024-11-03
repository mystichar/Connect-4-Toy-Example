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

        # Compile the CUDA kernel code and store the module and function
        self.mod = SourceModule("""
    // Define constants
    #define MAX_DEPTH 16      // Adjust as needed
    #define BOARD_SIZE 42
    #define NUM_FILTERS 69
    #define ROWS 6
    #define COLS 7
    #define INVALID_SEQUENCE -2
    #define RED_WIN 1
    #define YELLOW_WIN -1
    #define UNDECIDED 0
    #define SEQUENCES_PER_THREAD 16  // Adjust as needed

    // Declare solution filters in constant memory
    __constant__ int solution_filters_const[NUM_FILTERS * BOARD_SIZE];

    extern "C" __global__ void simulate_and_evaluate(
        const int *valid_moves,        // Array of valid moves (columns)
        const int num_valid_moves,     // Number of valid moves
        const int depth,               // Search depth
        int *results,                  // Output array for results (size: num_sequences in batch)
        const int *boards_initial,     // Initial board state
        const unsigned long long batch_start_idx,  // Starting index for this batch
        const unsigned long long num_sequences     // Number of sequences in this batch
    ) {
        unsigned long long thread_id = blockIdx.x * blockDim.x + threadIdx.x;
        unsigned long long total_threads = gridDim.x * blockDim.x;

        // Each thread simulates multiple sequences to increase GPU utilization
        for (unsigned long long idx = thread_id * SEQUENCES_PER_THREAD; idx < num_sequences; idx += total_threads * SEQUENCES_PER_THREAD) {
            for (int seq_offset = 0; seq_offset < SEQUENCES_PER_THREAD; seq_offset++) {
                unsigned long long idx_in_batch = idx + seq_offset;
                if (idx_in_batch >= num_sequences) break;
                unsigned long long sequence_idx = batch_start_idx + idx_in_batch;

                // Initialize the board with the initial state
                int board[BOARD_SIZE];
                for (int i = 0; i < BOARD_SIZE; i++) {
                    board[i] = boards_initial[i];
                }

                // Generate the move sequence based on sequence_idx
                int sequence[MAX_DEPTH];
                unsigned long long temp_idx = sequence_idx;
                for (int d = depth - 1; d >= 0; d--) {
                    sequence[d] = valid_moves[temp_idx % num_valid_moves];
                    temp_idx /= num_valid_moves;
                }

                // Simulate the move sequence
                int current_color = 1;  // Starting color (1 for Red)
                bool valid_sequence = true;
                for (int d = 0; d < depth; d++) {
                    int col = sequence[d];
                    bool move_made = false;
                    // Find the lowest empty row in the column
                    for (int row = ROWS - 1; row >= 0; row--) {
                        int idx_board = row * COLS + col;
                        if (board[idx_board] == 0) {
                            board[idx_board] = current_color;
                            move_made = true;
                            break;
                        }
                    }
                    if (!move_made) {
                        // Column is full; invalid sequence
                        valid_sequence = false;
                        break;
                    }
                    // Switch player
                    current_color = -current_color;
                }

                if (!valid_sequence) {
                    results[idx_in_batch] = INVALID_SEQUENCE;
                    continue;
                }

                // Evaluate the board state for a win
                int result = UNDECIDED;

                // Iterate over the solution filters
                for (int f = 0; f < NUM_FILTERS; f++) {
                    const int *filter = &solution_filters_const[f * BOARD_SIZE];
                    bool match_red = true;
                    bool match_yellow = true;

                    // Check for a match
                    for (int i = 0; i < BOARD_SIZE; i++) {
                        if (filter[i] == 1) {
                            if (board[i] != 1) {
                                match_red = false;
                            }
                            if (board[i] != -1) {
                                match_yellow = false;
                            }
                        }
                    }

                    if (match_red) {
                        result = RED_WIN;
                        break;
                    }
                    if (match_yellow) {
                        result = YELLOW_WIN;
                        break;
                    }
                }

                results[idx_in_batch] = result;
            }
        }
    }
"""
        )


        # Copy solution filters to constant memory on the GPU once
        self.solution_filters_const, _ = self.mod.get_global('solution_filters_const')
        drv.memcpy_htod(self.solution_filters_const, self.solution_filters.flatten().astype(np.int32))

        # Store the function for reuse
        self.func = self.mod.get_function("simulate_and_evaluate")

        # Initialize variables to keep track of previous valid moves and board state
        self.valid_moves_array_prev = None
        self.valid_moves_gpu = None
        self.boards_initial_prev = None
        self.boards_initial_gpu = None

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
        color = self.check_move_color()
        valid_moves = self.get_valid_moves()
        move_statistics = {}

        num_valid_moves = len(valid_moves)
        num_sequences = num_valid_moves ** depth

        if num_sequences == 0:
            return move_statistics  # No moves to evaluate

        # Prepare data for GPU
        valid_moves_array = np.array(valid_moves, dtype=np.int32)
        boards_initial = self.board.flatten().astype(np.int32)

        # Copy data to GPU only if necessary
        if self.valid_moves_gpu is None or not np.array_equal(self.valid_moves_array_prev, valid_moves_array):
            if self.valid_moves_gpu is not None:
                self.valid_moves_gpu.free()
            self.valid_moves_gpu = drv.mem_alloc(valid_moves_array.nbytes)
            drv.memcpy_htod(self.valid_moves_gpu, valid_moves_array)
            self.valid_moves_array_prev = valid_moves_array.copy()

        if self.boards_initial_gpu is None or not np.array_equal(self.boards_initial_prev, boards_initial):
            if self.boards_initial_gpu is not None:
                self.boards_initial_gpu.free()
            self.boards_initial_gpu = drv.mem_alloc(boards_initial.nbytes)
            drv.memcpy_htod(self.boards_initial_gpu, boards_initial)
            self.boards_initial_prev = boards_initial.copy()

        func = self.func  # Use precompiled function

        # Batch processing
        max_sequences_per_batch = 10**7  # Adjust based on your GPU's memory capacity
        total_batches = (num_sequences + max_sequences_per_batch - 1) // max_sequences_per_batch

        block_size = 512  # Adjust as needed
        SEQUENCES_PER_THREAD = 4  # Adjust as needed

        # Initialize the overall results array
        results_array = np.zeros(num_sequences, dtype=np.int32)

        for batch_idx in range(total_batches):
            batch_start = batch_idx * max_sequences_per_batch
            batch_end = min(num_sequences, (batch_idx + 1) * max_sequences_per_batch)
            batch_size = batch_end - batch_start

            # Allocate per-batch results array using pinned memory
            batch_results_array = drv.pagelocked_empty(batch_size, dtype=np.int32)
            results_gpu = drv.mem_alloc(batch_results_array.nbytes)

            num_threads = (batch_size + SEQUENCES_PER_THREAD - 1) // SEQUENCES_PER_THREAD
            grid_size = (num_threads + block_size - 1) // block_size

            # Launch the kernel for this batch
            func(
                self.valid_moves_gpu,
                np.int32(num_valid_moves),
                np.int32(depth),
                results_gpu,
                self.boards_initial_gpu,
                np.uint64(batch_start),    # batch_start_idx
                np.uint64(batch_size),     # num_sequences in this batch
                block=(block_size, 1, 1),
                grid=(grid_size, 1)
            )

            # Retrieve results for this batch
            drv.memcpy_dtoh(batch_results_array, results_gpu)

            # Copy batch results into the overall results array
            results_array[batch_start:batch_end] = batch_results_array

            # Free per-batch results_gpu
            results_gpu.free()

        # Aggregate results based on the initial move
        move_results = {}
        for idx in range(num_sequences):
            result = results_array[idx]
            if result == -2:
                continue  # Skip invalid sequences

            temp_idx = idx
            initial_move_idx = 0
            for d in range(depth):
                initial_move_idx = temp_idx % num_valid_moves
                temp_idx //= num_valid_moves

            initial_move = valid_moves[initial_move_idx]

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
