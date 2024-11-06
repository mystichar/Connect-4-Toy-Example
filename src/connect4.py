import numpy as np
import networkx as nx
import cirq
import cirq_pasqal
from cirq_pasqal import PasqalDevice

class Connect4Quantum:
    def __init__(self):
        # Initialize board dimensions
        self.rows = 6
        self.cols = 7
        self.board = np.zeros((self.rows, self.cols), dtype=int)

        # Initialize the game graph
        self.game_graph = nx.DiGraph()

        # Define qubits for quantum simulation (one per board cell)
        # Using NamedQubit as required by PasqalDevice
        self.qubits = [cirq.NamedQubit(f'q_{row}_{col}') for row in range(self.rows) for col in range(self.cols)]

        # Initialize Pasqal device without 'control_radius'
        self.device = PasqalDevice(qubits=self.qubits)

        # Initialize Cirq simulator
        self.simulator = cirq.Simulator()

    def check_move_color(self, board=None):
        board = self.board if board is None else board
        # Determine turn based on the piece count; 1 if even (Red), -1 if odd (Yellow)
        piece_count = np.count_nonzero(board)
        return 1 if piece_count % 2 == 0 else -1

    def get_valid_moves(self, board=None):
        board = self.board if board is None else board
        # Valid moves are columns where the top cell is empty
        return [col for col in range(self.cols) if board[0, col] == 0]

    def apply_move(self, board, col, color):
        # Place the piece in the lowest available row in the selected column
        for row in reversed(range(self.rows)):
            if board[row, col] == 0:
                board[row, col] = color
                return row, col  # Return the position where the piece was placed
        return None  # The column is full

    def is_full(self, board):
        # The board is full if there are no empty cells in the top row
        return np.all(board[0, :] != 0)

    def check_winner(self, board, color, last_row, last_col):
        """
        Checks if the last move at (last_row, last_col) created a winning sequence for the given color.
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
            r, c = last_row + dr, last_col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r += dr
                c += dc

            # Check in the negative direction
            r, c = last_row - dr, last_col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and board[r, c] == color:
                count += 1
                if count >= 4:
                    return True
                r -= dr
                c -= dc

        return False

    def get_game_result(self, board, color, last_row, last_col):
        """
        Check for a game result after the last move.
        """
        if self.check_winner(board, color, last_row, last_col):
            return "red_win" if color == 1 else "yellow_win"
        elif self.is_full(board):
            return "tie"
        else:
            return "undecided"

    def build_game_tree(self, depth):
        """
        Builds the game tree up to a certain depth using recursive traversal.
        """
        initial_state = self.board.copy()
        initial_state_tuple = tuple(initial_state.flatten())
        self.game_graph.clear()
        self.game_graph.add_node(initial_state_tuple)
        self._build_tree_recursive(initial_state, depth, initial_state_tuple)

    def _build_tree_recursive(self, board, depth, parent_state_tuple):
        if depth == 0:
            return
        color = self.check_move_color(board)
        valid_moves = self.get_valid_moves(board)

        for move in valid_moves:
            new_board = board.copy()
            result = self.apply_move(new_board, move, color)
            if result is None:
                continue  # Skip if the move is invalid
            new_state_tuple = tuple(new_board.flatten())
            if new_state_tuple in self.game_graph:
                # Avoid cycles
                self.game_graph.add_edge(parent_state_tuple, new_state_tuple, move=move, player=color)
                continue
            self.game_graph.add_node(new_state_tuple)
            self.game_graph.add_edge(parent_state_tuple, new_state_tuple, move=move, player=color)
            last_row, last_col = result
            game_result = self.get_game_result(new_board, color, last_row, last_col)
            if game_result != "undecided":
                self.game_graph.nodes[new_state_tuple]['result'] = game_result
            else:
                self._build_tree_recursive(new_board, depth - 1, new_state_tuple)

    def evaluate_move_statistics(self, depth=4, batch_size=100):
        """
        Evaluates move statistics using quantum circuits simulated with Cirq and Pasqal.

        Args:
            depth (int): The depth of the game tree to explore.
            batch_size (int): The number of move sequences to process in each batch.
        """
        color = self.check_move_color()
        valid_moves = self.get_valid_moves()
        move_statistics = {}

        if not valid_moves:
            return move_statistics  # No moves to evaluate

        # Build the game tree up to the specified depth
        self.build_game_tree(depth)

        # Get all possible move sequences up to the specified depth
        paths = []
        for target_depth in range(1, depth + 1):
            for path in self._get_paths_of_length(target_depth):
                paths.append(path)

        total_sequences = len(paths)
        print(f"Total move sequences to evaluate: {total_sequences}")

        # Process move sequences in batches
        for batch_start in range(0, total_sequences, batch_size):
            batch_paths = paths[batch_start:batch_start + batch_size]
            circuits = []
            move_indices = []
            path_end_states = []

            for path in batch_paths:
                circuit, initial_move, end_state = self._create_circuit_for_path(path)
                circuits.append(circuit)
                move_indices.append(initial_move)
                path_end_states.append(end_state)

            # Simulate the batch of circuits with one repetition each
            results = self.simulator.run_batch(circuits, repetitions=1)

            # Process results
            for i, result_list in enumerate(results):
                move = move_indices[i]
                result = result_list[0]  # Since we have repetitions=1
                measurements = result.measurements['m']
                outcome = self._determine_outcome(measurements, path_end_states[i])
                if move not in move_statistics:
                    move_statistics[move] = {'red_win': 0, 'yellow_win': 0, 'tie': 0, 'undecided': 0}
                move_statistics[move][outcome] += 1

        # Calculate percentages
        for move in move_statistics:
            stats = move_statistics[move]
            total = sum(stats.values())
            percentages = {key: (value / total) * 100 if total > 0 else 0 for key, value in stats.items()}
            move_statistics[move] = {'percentages': percentages}

        return move_statistics

    def _get_paths_of_length(self, length):
        """
        Get all paths from the root node to nodes at the specified depth (length).
        """
        initial_state_tuple = tuple(self.board.flatten())
        paths = []
        queue = [(initial_state_tuple, [initial_state_tuple])]

        while queue:
            (vertex, path) = queue.pop(0)
            if len(path) - 1 == length:
                paths.append(path)
            elif len(path) - 1 < length:
                for neighbor in self.game_graph.successors(vertex):
                    queue.append((neighbor, path + [neighbor]))

        return paths

    def _create_circuit_for_path(self, path):
        circuit = cirq.Circuit()
        move_sequence = []
        color_sequence = []

        # Reconstruct the move sequence from the edges
        for i in range(len(path) - 1):
            parent = path[i]
            child = path[i + 1]
            edge_data = self.game_graph.get_edge_data(parent, child)
            move_sequence.append(edge_data['move'])
            color_sequence.append(edge_data['player'])

        initial_move = move_sequence[0]
        end_state = np.array(path[-1]).reshape(self.rows, self.cols)

        # Apply gates to represent the move sequence
        for idx, move in enumerate(move_sequence):
            color = color_sequence[idx]
            # Get the move position (row, col) in the board
            parent_state = np.array(path[idx]).reshape(self.rows, self.cols)
            child_state = np.array(path[idx + 1]).reshape(self.rows, self.cols)
            diff = child_state - parent_state
            changed_indices = np.argwhere(diff != 0)

            for pos in changed_indices:
                row, col = pos
                qubit = cirq.NamedQubit(f'q_{row}_{col}')
                if color == 1:
                    # Red player's move: apply an X gate
                    circuit.append(cirq.X(qubit))
                else:
                    # Yellow player's move: apply an X and Z gate to represent -1
                    circuit.append([cirq.X(qubit), cirq.Z(qubit)])

        # Measure all qubits
        circuit.append(cirq.measure(*self.qubits, key='m'))

        return circuit, initial_move, end_state
                    
    def _determine_outcome(self, measurements, end_state):
        """
        Determine the game outcome based on the qubit measurements.

        Args:
            measurements (np.ndarray): The measurement results of the qubits.
            end_state (np.ndarray): The expected end state of the board.

        Returns:
            str: The game outcome ('red_win', 'yellow_win', 'tie', or 'undecided').
        """
        # Reconstruct the board state from measurements
        board_state = np.zeros((self.rows, self.cols), dtype=int)

        for i, qubit in enumerate(self.qubits):
            # Parse row and column from qubit name (e.g., "q_0_0" to get row=0, col=0)
            _, row, col = qubit.name.split('_')
            row, col = int(row), int(col)

            # Access measurement result carefully
            try:
                # If measurements[i] is a single-element array, retrieve the element
                meas = measurements[i][0] if isinstance(measurements[i], np.ndarray) else measurements[i]
            except IndexError:
                # Handle cases where measurements[i] does not exist as expected
                meas = measurements[0] if measurements.size == 1 else 0

            if meas == 1:
                # Assign color based on the expected end_state
                board_state[row, col] = end_state[row, col]

        # Now, check for a win in the board_state
        last_move_row, last_move_col = self._get_last_move_position(end_state)
        if last_move_row is None:
            return 'undecided'

        last_color = end_state[last_move_row, last_move_col]
        if self.check_winner(board_state, last_color, last_move_row, last_move_col):
            return 'red_win' if last_color == 1 else 'yellow_win'
        elif self.is_full(board_state):
            return 'tie'
        else:
            return 'undecided'


    def _get_last_move_position(self, end_state):
        """
        Find the position of the last move based on the difference from the initial board.

        Args:
            end_state (np.ndarray): The final state of the board after the move sequence.

        Returns:
            tuple: (row, col) of the last move, or (None, None) if not found.
        """
        initial_state = self.board
        diff = end_state - initial_state
        changed_indices = np.argwhere(diff != 0)
        if changed_indices.size == 0:
            return None, None
        # The last move is the last change made
        last_move_pos = changed_indices[-1]
        return last_move_pos[0], last_move_pos[1]

    def __str__(self):
        color_map = {0: ' . ', 1: ' R ', -1: ' Y '}
        string = ''
        for row in self.board:
            string += '|' + ''.join([color_map[cell] for cell in row]) + '|\n'
        string += '  ' + '  '.join(map(str, range(self.cols))) + '\n'
        return string
