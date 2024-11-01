# main.py

import torch
from connect4_game import Connect4Game
from connect4_net import Connect4Net
from mcts import MCTSNode, run_mcts

def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    batch_size = 256  # Adjust based on GPU memory
    num_simulations = 100  # Number of MCTS simulations
    num_games = 1  # Number of games to play
    net = Connect4Net().to(device)
    # Optionally load a pre-trained model
    # net.load_state_dict(torch.load('connect4_model.pth'))
    
    for game_idx in range(num_games):
        game = Connect4Game(batch_size=batch_size, device=device)
        root = MCTSNode(game)
        while not game.game_over.all():
            run_mcts(root, net, num_simulations, device=device)
            # Select the move with the highest visit count
            max_visits = -1
            best_move = None
            for action, child in root.children.items():
                if child.visit_count > max_visits:
                    max_visits = child.visit_count
                    best_move = action
            # Apply the best move
            moves = torch.full((batch_size,), best_move, device=device)
            game.apply_move(moves)
            # Move to the next node
            if best_move in root.children:
                root = root.children[best_move]
                root.parent = None  # Remove reference to parent to save memory
            else:
                root = MCTSNode(game)
            # Optionally, print or log the board state
            # ...

        # Game over, evaluate result
        # ...

if __name__ == '__main__':
    main()
