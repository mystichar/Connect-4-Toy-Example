import pytest
from .connect4 import Connect4Graph
def print_board(graph, rows, cols):
    for row in range(rows):
        row_str = ''
        for col in range(cols):
            cell = graph.nodes[(row, col)]['state']
            if cell == 1:
                row_str += 'R '  # Red
            elif cell == -1:
                row_str += 'Y '  # Yellow
            else:
                row_str += '. '  # Empty
        print(row_str)
    print('\n')


@pytest.fixture
def game():
    """Fixture to initialize a new Connect4 game."""
    return Connect4Graph()

def test_initialize_graph(game):
    """Test that the board initializes with all cells empty (state = 0)."""
    for row in range(game.rows):
        for col in range(game.cols):
            assert game.graph.nodes[(row, col)]['state'] == 0, f"Cell ({row}, {col}) should be empty"

def test_get_valid_moves_initial(game):
    """Test that get_valid_moves returns all columns initially."""
    expected_moves = list(range(game.cols))  # All columns should be available at the start
    assert game.get_valid_moves() == expected_moves, "All columns should be available at the start"

def test_apply_move_updates_state(game):
    """Test that apply_move updates the board state and returns the correct position."""
    col = 3
    color = 1  # Red
    row, _ = game.apply_move(game.graph, col, color)  # Apply move in column 3
    assert game.graph.nodes[(row, col)]['state'] == color, f"Cell ({row}, {col}) should be {color}"

def test_get_valid_moves_after_move(game):
    """Test get_valid_moves updates correctly after a move is applied."""
    col = 3
    color = 1  # Red
    game.apply_move(game.graph, col, color)  # Apply move in column 3
    assert col in game.get_valid_moves(), "Column should still be available until full"
    
    # Fill the column
    for _ in range(game.rows - 1):
        game.apply_move(game.graph, col, color)
    
    # Now column should be full and no longer in valid moves
    assert col not in game.get_valid_moves(), "Column should not be available when full"

def test_full_column_no_moves(game):
    """Test that apply_move returns None for a full column."""
    col = 4
    color = 1
    # Fill the column
    for _ in range(game.rows):
        game.apply_move(game.graph, col, color)
    
    assert game.apply_move(game.graph, col, color) is None, "apply_move should return None for a full column"

def test_check_winner_horizontal(game):
    """Test horizontal win condition."""
    color = 1
    last_row = None
    last_col = None
    for col in range(4):  # Apply four moves in columns 0 to 3
        row, col = game.apply_move(game.graph, col, color)
        last_row, last_col = row, col
    assert game.check_winner(game.graph, last_row, last_col, color), "Horizontal win condition should be detected"
def test_check_winner_diagonal(game):
    """Test diagonal win condition (bottom-left to top-right for Red)."""
    color = 1  # Red

    # Apply moves to create a diagonal from (5, 0) to (2, 3)
    game.apply_move(game.graph, 0, color)   # Move 1: Red at (5, 0)
    
    game.apply_move(game.graph, 1, -color)  # Move 2: Yellow at (5, 1)
    game.apply_move(game.graph, 1, color)   # Move 3: Red at (4, 1)
    
    game.apply_move(game.graph, 2, -color)  # Move 4: Yellow at (5, 2)
    game.apply_move(game.graph, 2, -color)  # Move 5: Yellow at (4, 2)
    game.apply_move(game.graph, 2, color)   # Move 6: Red at (3, 2)
    
    game.apply_move(game.graph, 3, -color)  # Move 7: Yellow at (5, 3)
    game.apply_move(game.graph, 3, -color)  # Move 8: Yellow at (4, 3)
    game.apply_move(game.graph, 3, -color)  # Move 9: Yellow at (3, 3)
    row, col = game.apply_move(game.graph, 3, color)   # Move 10: Red at (2, 3)

    # Now, Red has pieces at positions:
    # (5, 0), (4, 1), (3, 2), (2, 3) forming a diagonal

    # Print the board to verify placement
    print_board(game.graph, game.rows, game.cols)

    assert game.check_winner(game.graph, row, col, color), "Diagonal win condition should be detected"

def test_check_winner_diagonal(game):
    """Test diagonal win condition."""
    color = 1
    # Build up the board to create a diagonal from bottom-left to top-right
    game.apply_move(game.graph, 0, -color)  # Move 1
    game.apply_move(game.graph, 1, -color)  # Move 2
    game.apply_move(game.graph, 1, color)   # Move 3
    game.apply_move(game.graph, 2, -color)  # Move 4
    game.apply_move(game.graph, 2, color)   # Move 5
    game.apply_move(game.graph, 2, color)   # Move 6
    # Capture the row and col of the last move
    row, col = game.apply_move(game.graph, 3, color)  # Move 7
    assert game.check_winner(game.graph, row, col, color), "Diagonal win condition should be detected"


def test_get_game_result_tie(game):
    """Test get_game_result returns 'tie' when the board is full and no winner exists."""
    color = 1
    # Fill the board without creating any winning condition
    for col in range(game.cols):
        for row in range(game.rows):
            game.apply_move(game.graph, col, color)
            color *= -1  # Alternate colors
    assert game.is_full(game.graph), "The board should be full"
    assert game.get_game_result(game.graph, color, 0, 0) == "tie", "Game result should be 'tie' when the board is full without a winner"
