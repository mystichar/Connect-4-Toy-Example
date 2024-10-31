# test_gravity.py
import pytest
from .connect4 import Connect4Board, Connect4

def test_gravity_empty_column():
    board_data = {
        (5, 0): 0,
        (4, 0): 0,
        (3, 0): 0,
        (2, 0): 0,
        (1, 0): 0,
        (0, 0): None,  # None as an invalid spot
    }
    board_model = Connect4Board(board=board_data)
    game = Connect4(board_model)
    game.apply_gravity()
    assert game.get_board_state() == board_data  # Nothing should change in an empty column

def test_gravity_single_piece():
    board_data = {
        (5, 0): 0,
        (4, 0): 0,
        (3, 0): 1,
        (2, 0): 0,
        (1, 0): 0,
        (0, 0): None,
    }
    expected_board = {
        (5, 0): 1,
        (4, 0): 0,
        (3, 0): 0,
        (2, 0): 0,
        (1, 0): 0,
        (0, 0): None,
    }
    board_model = Connect4Board(board=board_data)
    game = Connect4(board_model)
    game.apply_gravity()
    assert game.get_board_state() == expected_board

def test_gravity_multiple_pieces():
    board_data = {
        (5, 0): 0,
        (4, 0): 1,
        (3, 0): -1,
        (2, 0): 1,
        (1, 0): 0,
        (0, 0): None,
    }
    expected_board = {
        (5, 0): 1,
        (4, 0): -1,
        (3, 0): 1,
        (2, 0): 0,
        (1, 0): 0,
        (0, 0): None,
    }
    board_model = Connect4Board(board=board_data)
    game = Connect4(board_model)
    game.apply_gravity()
    assert game.get_board_state() == expected_board
    
def test_gravity_with_none_cells():
    board_data = {
        (5, 0): 0,
        (4, 0): 1,
        (3, 0): None,
        (2, 0): -1,
        (1, 0): 0,
        (0, 0): 1,
    }
    expected_board = {
        (5, 0): 1,
        (4, 0): 0,
        (3, 0): None,
        (2, 0): -1,
        (1, 0): 1,
        (0, 0): 0,
    }
    board_model = Connect4Board(board=board_data)
    game = Connect4(board_model)
    game.apply_gravity()
    assert game.get_board_state() == expected_board

def test_gravity_mixed_column():
    board_data = {
        (5, 1): -1,
        (4, 1): 1,
        (3, 1): 0,
        (2, 1): 1,
        (1, 1): None,
        (0, 1): 0,
    }
    expected_board = {
        (5, 1): -1,
        (4, 1): 1,
        (3, 1): 1,
        (2, 1): 0,
        (1, 1): None,
        (0, 1): 0,
    }
    board_model = Connect4Board(board=board_data)
    game = Connect4(board_model)
    game.apply_gravity()
    assert game.get_board_state() == expected_board

def test_gravity_no_changes():
    board_data = {
        (5, 2): 1,
        (4, 2): 1,
        (3, 2): -1,
        (2, 2): 0,
        (1, 2): None,
        (0, 2): None,
    }
    expected_board = board_data  # Gravity shouldn't change anything
    board_model = Connect4Board(board=board_data)
    game = Connect4(board_model)
    game.apply_gravity()
    assert game.get_board_state() == expected_board
