import pickle
from multiprocessing import shared_memory, Lock
from concurrent.futures import ProcessPoolExecutor, as_completed

class Connect4:
    process_pool = ProcessPoolExecutor(max_workers=64)
    PARALLEL_DEPTH_THRESHOLD = 1  # Adjust threshold for task parallelism
    shm_lock = Lock()  # Lock to manage shared memory access

    def __init__(self):
        self.rows = 6
        self.cols = 7
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Initialize shared memory with an appropriate size
        self.shm = shared_memory.SharedMemory(create=True, size=10**7)
        self.memo = {}  # Local cache within each process

    def store_in_shared_memory(self, key, value):
        """Store data in shared memory with serialization."""
        serialized_data = pickle.dumps({key: value})
        with self.shm_lock:
            self.shm.buf[:len(serialized_data)] = serialized_data

    def load_from_shared_memory(self, key):
        """Load data from shared memory with deserialization."""
        with self.shm_lock:
            serialized_data = self.shm.buf[:]
            if not serialized_data or serialized_data[0] == 0:
                # Shared memory buffer is empty or uninitialized
                return None
            try:
                loaded_data = pickle.loads(serialized_data)
                return loaded_data.get(key)
            except pickle.UnpicklingError:
                # Handle unpickling error if data is corrupted
                return None

    def evaluate_move_statistics(self, depth=4):
        color = self.check_move_color()
        valid_moves = self.get_valid_moves(self.board)
        move_statistics = {}

        futures = []
        task_count = 0  # Track number of tasks submitted

        for col in valid_moves:
            new_board = [row[:] for row in self.board]
            row, col_pos = self.apply_move(new_board, col, color)
            # Submit top-level tasks to the process pool
            futures.append(self.process_pool.submit(
                self.evaluate_single_move,
                new_board,
                depth - 1,
                -color,
                col,
            ))
            task_count += 1  # Increment task counter

        for future in as_completed(futures):
            col, stats = future.result()
            total = sum(stats.values())
            percentages = {key: (stats.get(key, 0) / total) * 100 if total > 0 else 0
                           for key in ['red_win', 'yellow_win', 'tie', 'undecided']}
            move_statistics[col] = {'percentages': percentages}

        # Report the number of workers used (tasks submitted)
        print(f"Tasks submitted to the process pool: {task_count}")
        print(f"Max workers available: {self.process_pool._max_workers}")

        return move_statistics

    def evaluate_single_move(self, board, depth, color, col):
        stats = self.simulate_move_tree_statistics(board, depth, color)
        return col, stats

    def simulate_move_tree_statistics(self, board, depth, current_color):
        result = self.get_game_result_after_last_move(board, -current_color)
        if result != "undecided" or depth == 0:
            return {result: 1}

        # Use a hashable key for memoization
        board_tuple = tuple(map(tuple, board))
        key = (board_tuple, current_color, depth)

        # Check local memo first
        if key in self.memo:
            return self.memo[key]

        # Try loading from shared memory
        shared_result = self.load_from_shared_memory(key)
        if shared_result:
            self.memo[key] = shared_result
            return shared_result

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
            for k in results:
                results[k] += outcome.get(k, 0)

        # Store result in both local memo and shared memory
        self.memo[key] = results
        self.store_in_shared_memory(key, results)
        return results

    def cleanup(self):
        """Release shared memory resources."""
        self.shm.close()
        self.shm.unlink()

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
    
    def apply_move(self, board, col, color):
        # Place the piece in the lowest available row in the selected column
        for row in reversed(range(self.rows)):
            if board[row][col] == 0:
                board[row][col] = color
                return row, col  # Return the position where the piece was placed
        return None  # The column is full; should not happen if checked before
