import cirq
import random

# Create a 3x3 grid of qubits to represent the board
board = [[cirq.GridQubit(i, j) for j in range(3)] for i in range(3)]

# Initialize a circuit
circuit = cirq.Circuit()

# Function to represent a move: X or O based on gate choice
def make_move(circuit, qubit, player):
    if player == "X":
        # Pauli-X gate as an example for "X"
        circuit.append(cirq.X(qubit))
    elif player == "O":
        # Hadamard gate as an example for "O"
        circuit.append(cirq.H(qubit))

# Random player moves (for demo purposes)
for _ in range(5):
    i, j = random.randint(0, 2), random.randint(0, 2)
    player = "X" if _ % 2 == 0 else "O"
    make_move(circuit, board[i][j], player)

# Add measurements to simulate ending the game and reading board state
for row in board:
    for qubit in row:
        circuit.append(cirq.measure(qubit, key=str(qubit)))

# Run simulation
simulator = cirq.Simulator()
result = simulator.run(circuit, repetitions=1)

# Print results
print("Board state after random moves:")
for i in range(3):
    print([result.measurements[str(board[i][j])][0][0] for j in range(3)])
