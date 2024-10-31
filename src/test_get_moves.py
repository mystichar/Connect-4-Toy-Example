# test_get_moves.py
import pytest
from .connect4 import Connect4

def test_get_moves_empty_board():
    game = Connect4()
    color = game.check_move_color()
    potential_states = game.get_valid_moves()
    
    # Expect each potential state to have one piece in the bottom row
    for col, new_board in enumerate(potential_states):
        assert new_board[(0, col)] == color

def test_get_moves_partially_filled_board():
    game = Connect4()
    
    # Modify board to match partially filled test case
    game.board.update({
        (0, 0): 1, (1, 0): 1, (2, 0): 1, (3, 0): 1, (4, 0): 1,  # Column 0 is full
        (0, 1): 0, (1, 1): -1, (2, 1): 1, (3, 1): 1, (4, 1): 0,  # Column 1 has a valid move at row 0
        (0, 2): 0, (1, 2): -1, (2, 2): 0, (3, 2): 0, (4, 2): 0,  # Column 2 has a valid move at row 0
    })
    
    color = game.check_move_color()
    potential_states = game.get_valid_moves()
    
    # Verify correct placement of pieces
    assert potential_states[0][(0, 1)] == color
    assert potential_states[1][(0, 2)] == color

def test_get_moves_with_none_cells():
    game = Connect4()
    
    # Modify board to include None cells
    game.board.update({
        (0, 0): 0, (1, 0): 0, (2, 0): -1, (3, 0): None, (4, 0): None,
        (0, 1): 1, (1, 1): 0, (2, 1): 1, (3, 1): -1, (4, 1): None,
    })
    
    color = game.check_move_color()
    potential_states = game.get_valid_moves()
    
    # Verify that moves avoid None cells and add pieces correctly
    assert potential_states[0][(0, 0)] == color  # Move in column 0

def test_get_moves_full_board():
    game = Connect4()
    
    # Fill the board
    game.board.update({
        (row, col): 1 if (row + col) % 2 == 0 else -1
        for row in range(5)
        for col in range(7)
    })
    
    # Expect no valid moves
    assert game.get_valid_moves() == []
