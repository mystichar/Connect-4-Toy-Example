# objective: brute force calculate the probability of winning based on each move
from .board_model import Connect4Board

class Connect4:
    def __init__(self, board_model: Connect4Board = None):
        if board_model:
            self.board = board_model.board
        else:
            # Initialize a 5-tall by 7-wide empty board
            self.board = {(row, col): 0 for row in range(5) for col in range(7)}

    def check_move_color(self):
        # Determine turn based on piece count; default to 1 if even, else -1
        piece_count = sum(1 for cell in self.board.values() if cell != 0)
        return 1 if piece_count % 2 == 0 else -1

    def get_valid_moves(self, color=None):
        if color is None:
            color = self.check_move_color()
            
        max_row = max(row for row, _ in self.board.keys())
        max_col = max(col for _, col in self.board.keys())
        
        potential_states = []
        
        for col in range(max_col + 1):
            for row in range(max_row + 1):
                cell = self.board.get((row, col), None)
                
                if cell == 0:
                    # Only apply move if no None cells are above it
                    above_cell = self.board.get((row + 1, col), None)
                    if above_cell is not None or row == max_row:
                        # Create a copy of the board with the new piece added
                        new_state = self.board.copy()
                        new_state[(row, col)] = color
                        potential_states.append(new_state)
                    break  # Stop after finding the first empty spot in this column
                elif cell is None:
                    break  # Stop checking if a None cell is encountered

        return potential_states

    def __str__(self) -> str:
        color_map = {
            0: " |",
            1: "\033[91m0\033[0m|",   # Red "0" for player 1
            -1: "\033[93m0\033[0m|"   # Yellow "0" for player -1
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

    def check_winner(self, color=None):
        if color is None:
            color = -1 * self.check_move_color()

        max_row = max(row for row, _ in self.board.keys())
        max_col = max(col for _, col in self.board.keys())
        
        # Directions: vertical, horizontal, diagonal down-right, diagonal down-left
        directions = [
            (1, 0),  # Vertical
            (0, 1),  # Horizontal
            (1, 1),  # Diagonal down-right
            (1, -1)  # Diagonal down-left
        ]
        
        for row in range(max_row + 1):
            for col in range(max_col + 1):
                if self.board.get((row, col)) == color:
                    for dr, dc in directions:
                        if self._check_four_in_a_row(row, col, dr, dc, color, max_row, max_col):
                            return True
        return False

    def _check_four_in_a_row(self, row, col, dr, dc, color, max_row, max_col):
        # Check boundaries and four consecutive pieces in the given direction
        for i in range(4):
            new_row = row + i * dr
            new_col = col + i * dc
            if new_row > max_row or new_row < 0 or new_col > max_col or new_col < 0:
                return False
            if self.board.get((new_row, new_col)) != color:
                return False
        return True

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
