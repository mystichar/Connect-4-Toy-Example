import pytest
from pydantic import ValidationError
from .board_model import Connect4Board  # replace 'connect4' with the actual module name

def test_valid_board():
    board_data = {
        (0, 0): 1,
        (0, 1): 0,
        (0, 2): -1,
        (1, 0): None
    }
    connect4_board = Connect4Board(board=board_data)
    assert connect4_board.board == board_data

def test_invalid_values():
    board_data = {
        (0, 0): 1,
        (0, 1): 0,
        (0, 2): 2,  # Invalid value
        (1, 0): None
    }
    with pytest.raises(ValidationError) as excinfo:
        Connect4Board(board=board_data)
    assert "Input should be less than or equal to 1" in str(excinfo.value)

def test_invalid_key():
    board_data = {
        0: 1,  # Invalid key
        (0, 1): 0,
        (1, 0): -1
    }
    with pytest.raises(ValidationError):
        Connect4Board(board=board_data)

def test_empty_board():
    board_data = {}
    connect4_board = Connect4Board(board=board_data)
    assert connect4_board.board == board_data

def test_none_values():
    board_data = {
        (0, 0): None,
        (1, 1): None,
        (2, 2): None
    }
    connect4_board = Connect4Board(board=board_data)
    assert connect4_board.board == board_data

def test_boundary_values():
    board_data = {
        (0, 0): 0,
        (0, 1): -1,
        (0, 2): 1,
        (1, 0): None
    }
    connect4_board = Connect4Board(board=board_data)
    assert connect4_board.board == board_data
