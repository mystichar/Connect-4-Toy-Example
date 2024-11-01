import networkx as nx

class Connect4Graph:
    def __init__(self):
        self.rows = 6
        self.cols = 7
        self.graph = nx.DiGraph()
        self.initialize_graph()

    def initialize_graph(self):
        for row in range(self.rows):
            for col in range(self.cols):
                node = (row, col)
                self.graph.add_node(node, state=0)  # 0 for empty, 1 for Red, -1 for Yellow
                # Add edges for potential connections (optional for game logic)
                if col + 1 < self.cols:  # Right
                    self.graph.add_edge(node, (row, col + 1))
                if row + 1 < self.rows:  # Down
                    self.graph.add_edge(node, (row + 1, col))
                if row + 1 < self.rows and col + 1 < self.cols:  # Diagonal down-right
                    self.graph.add_edge(node, (row + 1, col + 1))
                if row + 1 < self.rows and col - 1 >= 0:  # Diagonal down-left
                    self.graph.add_edge(node, (row + 1, col - 1))

    def reset_board(self):
        for node in self.graph.nodes:
            self.graph.nodes[node]['state'] = 0

    def apply_move(self, graph, col, color):
        # Place piece in the lowest available cell in the column, or return None if column is full
        for row in reversed(range(self.rows)):
            if graph.nodes[(row, col)]['state'] == 0:
                graph.nodes[(row, col)]['state'] = color
                return row, col  # Return the position where the piece was placed
        return None  # Column is full

    def get_valid_moves(self, graph=None):
        graph = graph or self.graph
        return [col for col in range(self.cols) if graph.nodes[(0, col)]['state'] == 0]

    def is_full(self, graph):
        return all(graph.nodes[(0, col)]['state'] != 0 for col in range(self.cols))

    def check_winner(self, graph, row, col, color, debug=False):
        # Define pairs of directions to check
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal down-right
            (1, -1)   # Diagonal down-left
        ]

        for dr, dc in directions:
            count = 1  # Start with the piece at (row, col)

            # Check in the positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and graph.nodes[(r, c)]['state'] == color:
                count += 1
                r += dr
                c += dc

            # Check in the negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and graph.nodes[(r, c)]['state'] == color:
                count += 1
                r -= dr
                c -= dc

            if debug:
                print(f"Debug: Total count in direction ({dr}, {dc}) from ({row}, {col}) is {count}")

            # If we have four or more in a row, return True for a win
            if count >= 4:
                if debug:
                    print(f"Debug: Winner detected for color {color} at starting position ({row}, {col})")
                return True

        return False

    def get_game_result(self, graph, color, row, col):
        if self.check_winner(graph, row, col, color):
            return "red_win" if color == 1 else "yellow_win"
        elif self.is_full(graph):
            return "tie"
        return "undecided"

    def evaluate_move_statistics(self, depth=4):
        color = 1 if sum(self.graph.nodes[node]['state'] != 0 for node in self.graph.nodes) % 2 == 0 else -1
        valid_moves = self.get_valid_moves()
        move_statistics = {}

        if not valid_moves:
            return {col: {'percentages': {'red_win': 0, 'yellow_win': 0, 'tie': 100, 'undecided': 0}} for col in range(self.cols)}

        for col in valid_moves:
            board_copy = self.graph.copy()
            move = self.apply_move(board_copy, col, color)
            if move:
                col, result = self.evaluate_single_move(board_copy, move, color, depth)
                if result == "red_win":
                    move_statistics[col] = {'percentages': {'red_win': 100, 'yellow_win': 0, 'tie': 0, 'undecided': 0}}
                elif result == "yellow_win":
                    move_statistics[col] = {'percentages': {'red_win': 0, 'yellow_win': 100, 'tie': 0, 'undecided': 0}}
                elif result == "tie":
                    move_statistics[col] = {'percentages': {'red_win': 0, 'yellow_win': 0, 'tie': 100, 'undecided': 0}}
                else:
                    move_statistics[col] = {'percentages': {'red_win': 0, 'yellow_win': 0, 'tie': 0, 'undecided': 100}}

        return move_statistics


    def evaluate_single_move(self, graph, move, color, depth):
        if move is None:
            return None, "invalid"

        row, col = move
        game_result = self.get_game_result(graph, color, row, col)
        if game_result != "undecided" or depth == 0:
            return col, game_result

        valid_moves = self.get_valid_moves(graph)
        if not valid_moves:
            return col, "tie"

        # Ensure depth decreases with each recursive call
        results = {"red_win": 0, "yellow_win": 0, "tie": 0, "undecided": 0}

        for next_col in valid_moves:
            next_graph = graph.copy()
            next_move = self.apply_move(next_graph, next_col, -color)
            if next_move:
                immediate_result = self.get_game_result(next_graph, -color, next_move[0], next_move[1])
                if immediate_result != "undecided":
                    results[immediate_result] += 1
                else:
                    _, outcome = self.evaluate_single_move(next_graph, next_move, -color, depth - 1)
                    results[outcome] += 1

        # Determine the result with the highest count
        max_result = max(results, key=results.get)
        return col, max_result

    def cleanup(self):
        pass
