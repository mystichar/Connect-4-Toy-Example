import pytest
from .connect4 import Connect4

def print_board_state(board, indent=""):
    color_map = {
        0: "_",
        1: "R",
        -1: "Y"
    }
    max_row = max(row for row, _ in board.keys())
    max_col = max(col for _, col in board.keys())

    for row in range(max_row, -1, -1):
        line = indent + "| "
        for col in range(max_col + 1):
            cell = board.get((row, col), 0)
            line += color_map[cell] + " "
        print(line)
    print()

def print_move_tree(node, depth=0):
    indent = "  " * depth
    move = f"Move: Column {node.get('move')}" if 'move' in node else "Root"
    result = node['result']
    print(f"{indent}{move}, Result: {result}")

    # Print the board state
    print_board_state(node['board'], indent)

    for child in node['children']:
        print_move_tree(child, depth + 1)
import pytest
from .connect4 import Connect4

# Helper functions to print board and move tree
def print_board_state(board, indent=""):
    color_map = {
        0: "_",
        1: "R",
        -1: "Y"
    }
    max_row = max(row for row, _ in board.keys())
    max_col = max(col for _, col in board.keys())

    for row in range(max_row, -1, -1):
        line = indent + "| "
        for col in range(max_col + 1):
            cell = board.get((row, col), 0)
            line += color_map[cell] + " "
        print(line)
    print()

def print_move_tree(node, depth=0):
    indent = "  " * depth
    move = f"Move: Column {node.get('move')}" if 'move' in node else "Root"
    result = node['result']
    print(f"{indent}{move}, Result: {result}")

    print_board_state(node['board'], indent)

    for child in node['children']:
        print_move_tree(child, depth + 1)

# Test cases
def test_immediate_win_with_smart_players():
    game = Connect4()
    # Set up a board where Red can win immediately in column 2
    game.board.update({
        (0, 2): 1, (1, 2): 1, (2, 2): 1,  # Three in a column for Red,
        (0,1): -1, (0, 0): -1, (0, 4): -1 # 3 spread out Y
    })
    stats = game.evaluate_move_statistics(depth=3, smart_players=True)

    print("Test: Immediate Win with Smart Players")
    try:
        assert stats[2]['percentages']['red_win'] == 100.0
    except AssertionError:
        print("Failed Immediate Win with Smart Players Test: Full Move Tree Below")
        print_move_tree(stats[2]['move_tree'])
        raise

def test_immediate_block_with_smart_players():
    game = Connect4()
    # Set up a board where Yellow must block Red in column 3
    game.board.update({
        (0, 3): 1, (1, 3): 1, (2, 3): 1  # Three in a column for Red
    })
    # It's Yellow's turn
    stats = game.evaluate_move_statistics(depth=3, smart_players=True)

    print("Test: Immediate Block with Smart Players")
    try:
        assert stats[3]['percentages']['red_win'] == 0.0
    except AssertionError:
        print("Failed Immediate Block with Smart Players Test: Full Move Tree Below")
        print_move_tree(stats[3]['move_tree'])
        raise

def test_complex_scenario_with_smart_players():
    game = Connect4()
    # Set up a board with a more complex scenario
    game.board.update({
        (0, 0): 1, (0, 1): -1, (0, 2): 1,
        (1, 0): -1, (1, 1): 1, (1, 2): -1,
        (2, 0): 1, (2, 1): -1  # Create a mixed board state
    })
    stats = game.evaluate_move_statistics(depth=3, smart_players=True)

    print("Test: Complex Scenario with Smart Players")
    try:
        # Check that statistics include reasonable values
        for col, move_stats in stats.items():
            percentages = move_stats['percentages']
            assert percentages['red_win'] >= 0.0
            assert percentages['yellow_win'] >= 0.0
            assert percentages['tie'] >= 0.0
            assert percentages['undecided'] >= 0.0
    except AssertionError:
        print("Failed Complex Scenario with Smart Players Test: Full Move Tree Below")
        for col, move_data in stats.items():
            print(f"Column {col}:")
            print_move_tree(move_data['move_tree'])
        raise

def test_near_tie_with_smart_players():
    game = Connect4()
    # Create a nearly full board with no winning positions left
    for row in range(5):
        for col in range(7):
            game.board[(row, col)] = 1 if (row + col) % 2 == 0 else -1

    stats = game.evaluate_move_statistics(depth=3, smart_players=True)

    print("Test: Near Tie with Smart Players")
    try:
        # Expect only ties or undecided outcomes in a nearly full board
        for col, move_data in stats.items():
            percentages = move_data['percentages']
            assert percentages['tie'] >= 0.0
            assert percentages['undecided'] >= 0.0
    except AssertionError:
        print("Failed Near Tie with Smart Players Test: Full Move Tree Below")
        for col, move_data in stats.items():
            print(f"Column {col}:")
            print_move_tree(move_data['move_tree'])
        raise
