__device__ int check_winner(int *board, int color, int rows, int cols, int last_row, int last_col) {
            int directions[4][2] = {
                {0, 1},   // Horizontal
                {1, 0},   // Vertical
                {1, 1},   // Diagonal /
                {1, -1}   // Diagonal 
            };
            for (int i = 0; i < 4; i++) {
                int dr = directions[i][0];
                int dc = directions[i][1];
                int count = 1;
                int r = last_row + dr;
                int c = last_col + dc;
                while (r >= 0 && r < rows && c >= 0 && c < cols && board[r * cols + c] == color) {
                    count++;
                    if (count >= 4) return 1;
                    r += dr;
                    c += dc;
                }
                r = last_row - dr;
                c = last_col - dc;
                while (r >= 0 && r < rows && c >= 0 && c < cols && board[r * cols + c] == color) {
                    count++;
                    if (count >= 4) return 1;
                    r -= dr;
                    c -= dc;
                }
            }
            return 0;  // Add this line
        }

        __device__ int is_full(int *board, int cols) {
            for (int c = 0; c < cols; c++) {
                if (board[c] == 0) return 0;
            }
            return 1;
        }

        __global__ void simulate_moves(int *boards, int *results, int *colors, int *last_rows, int *last_cols, int num_boards, int rows, int cols) {
            int idx = blockIdx.x * blockDim.x + threadIdx.x;
            if (idx >= num_boards) return;

            // Each thread handles one board
            int *board = &boards[idx * rows * cols];
            int color = colors[idx];
            int last_row = last_rows[idx];
            int last_col = last_cols[idx];

            // Initialize result counts
            int red_win = 0;
            int yellow_win = 0;
            int tie = 0;
            int undecided = 0;

            int result = 0;
            if (check_winner(board, -color, rows, cols, last_row, last_col)) {
                result = (-color == 1) ? 1 : -1;  // 1 for red win, -1 for yellow win
            } else if (is_full(board, cols)) {
                result = 2;  // Tie
            }

            if (result == 1) {
                red_win++;
            } else if (result == -1) {
                yellow_win++;
            } else if (result == 2) {
                tie++;
            } else {
                undecided++;
            }

            // Write results
            results[idx * 4 + 0] = red_win;
            results[idx * 4 + 1] = yellow_win;
            results[idx * 4 + 2] = tie;
            results[idx * 4 + 3] = undecided;
        }
