import pytest
from .connect4 import connect4  

# Test cases for check_win_brute_force
def test_horizontal_win():
    # Setup a board with a horizontal win for red (1) on the bottom row
    board = [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    game = connect4(board=board)
    assert game.check_win_brute_force(color=1) == True

def test_vertical_win():
    # Setup a board with a vertical win for yellow (-1)
    board = [
        [0, 0, 0, 0, 0, 0],
        [0, 0, -1, -1, -1, -1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    game = connect4(board=board)
    assert game.check_win_brute_force(color=-1) == True

def test_diagonal_down_right_win():
    # Setup a board with a diagonal down-right win for red (1)
    board = [
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    game = connect4(board=board)
    assert game.check_win_brute_force(color=1) == True

def test_diagonal_up_right_win():
    # Setup a board with a diagonal up-right win for yellow (-1)
    board = [
        [0, 0, 0, 0, 0, -1],
        [0, 0, 0, 0, -1, 0],
        [0, 0, 0, -1, 0, 0],
        [0, 0, -1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    game = connect4(board=board)
    assert game.check_win_brute_force(color=-1) == True

def test_no_win():
    # Setup a board with no winning condition
    board = [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, -1, 1, -1],
        [0, 0, -1, 1, -1, 1],
        [0, 0, 1, -1, 1, -1],
        [0, 0, -1, 1, -1, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    game = connect4(board=board)
    assert game.check_win_brute_force(color=1) == False
    assert game.check_win_brute_force(color=-1) == False

def test_mixed_win_conditions():
    # Setup a board with multiple possible winning lines for red (1)
    board = [
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    game = connect4(board=board)
    assert game.check_win_brute_force(color=1) == True
