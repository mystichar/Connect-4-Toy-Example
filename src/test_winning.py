# test_winning.py
import pytest
from .connect4 import Connect4

def test_no_winner_empty_board():
    game = Connect4()
    try:
        assert game.check_winner(1) is False
        assert game.check_winner(-1) is False
    except AssertionError:
        print("Board state:\n", game)
        raise

def test_vertical_win():
    game = Connect4()
    game.board.update({
        (0, 0): 1, (1, 0): 1, (2, 0): 1, (3, 0): 1  # Vertical win in column 0
    })
    try:
        assert game.check_winner(1) is True
        assert game.check_winner(-1) is False
    except AssertionError:
        print("Board state:\n", game)
        raise

def test_horizontal_win():
    game = Connect4()
    game.board.update({
        (0, 0): -1, (0, 1): -1, (0, 2): -1, (0, 3): -1  # Horizontal win in row 0
    })
    try:
        assert game.check_winner(-1) is True
        assert game.check_winner(1) is False
    except AssertionError:
        print("Board state:\n", game)
        raise

def test_diagonal_down_right_win():
    game = Connect4()
    game.board.update({
        (0, 0): 1, (1, 1): 1, (2, 2): 1, (3, 3): 1  # Diagonal down-right win
    })
    try:
        assert game.check_winner(1) is True
        assert game.check_winner(-1) is False
    except AssertionError:
        print("Board state:\n", game)
        raise

def test_diagonal_down_left_win():
    game = Connect4()
    game.board.update({
        (3, 0): -1, (2, 1): -1, (1, 2): -1, (0, 3): -1  # Diagonal down-left win
    })
    try:
        assert game.check_winner(-1) is True
        assert game.check_winner(1) is False
    except AssertionError:
        print("Board state:\n", game)
        raise

def test_double_win_with_mixed_pieces():
    game = Connect4()
    game.board.update({
        (0, 0): 1, (0, 1): -1, (0, 2): 1, (0, 3): -1,
        (1, 0): -1, (1, 1): 1, (1, 2): -1, (1, 3): 1,
        (2, 0): 1, (2, 1): -1, (2, 2): 1, (2, 3): -1,
        (3, 0): -1, (3, 1): 1, (3, 2): -1, (3, 3): 1,
    })
    try:
        assert game.check_winner(1) is True
        assert game.check_winner(-1) is True
    except AssertionError:
        print("Board state:\n", game)
        raise

def test_no_win_with_mixed_pieces():
    game = Connect4()
    # Adjusted board to avoid any winning sequence for either player
    game.board.update({
        (0, 0): 1, (0, 1): -1, (0, 2): 1, (0, 3): 0,
        (1, 0): -1, (1, 1): 1, (1, 2): -1, (1, 3): 1,
        (2, 0): 1, (2, 1): -1, (2, 2): 1, (2, 3): -1,
        (3, 0): -1, (3, 1): 1, (3, 2): -1, (3, 3): 0,  # Last piece changed to 0 to avoid a diagonal
    })
    try:
        assert game.check_winner(1) is False
        assert game.check_winner(-1) is False
    except AssertionError:
        print("Board state:\n", game)
        raise