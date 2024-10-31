# objective: brute force calculate the probability of winning based on each move

from copy import deepcopy

class connect4:
    def __init__(self, board) -> None:
        self.board_init = board
        self.board = board
        self.gen_heat = self.calculate_generic_heat_map()
        if not self.validate_board():
            print("Invalid Board")

    def __str__(self) -> str:
        color_map = {
            0: " |",
            1: "\033[91m0\033[0m|",
            -1: "\033[93m0\033[0m|"
        }
        
        # Determine board dimensions
        num_columns = len(self.board)
        num_rows = len(self.board[0]) if num_columns > 0 else 0

        # Build the display string row by row, starting from the top row (highest index)
        string = ""
        for row in range(num_rows - 1, -1, -1):
            string += "|"
            for col in range(num_columns):
                cell = self.board[col][row]
                string += color_map[cell]
            string += "\n"

        return string

    def check_move_color(self, board=None):
        board = self.board if not board else board
        piece_parity = 0 # if 0 then red's turn, if 1 then yellows
        for column in board:
            for cell in column:
                piece_parity += cell
        piece_mapping = {0:1, 1:-1}
        return piece_mapping[piece_parity]
    
    def validate_board(self, board=None):
        board = self.board if not board else board

        # Determine board dimensions
        num_columns = len(self.board)
        num_rows = len(self.board[0]) if num_columns > 0 else 0
        if num_columns < 4 and num_rows < 4:
            print("unwinnable board")
            return False
        i = 0
        for column in board:
            j = 0
            if len(column) != 5:
                print(f"invalidated on length of column {i}: length found {len(column)}")
                return False
            pillar_height = 0
            for cell in column:
                if cell != 0 and cell != 1 and cell != -1:
                    print(f"invalid cell value {j}: found value: {cell}")
                    return False
                if cell != 0:
                    if j > pillar_height:
                        print(f"Found unsupported cell in row {j} and column {i}: Column {i}: {column}, pillar: {pillar_height}")
                        return False
                    pillar_height += 1
                j += 1
            i += 1

        return True
    
    def find_move_options(self, board=None, open_columns=None):
        board = self.board if not board else board
        piece = self.check_move_color()
        moves = []
        options = {}

        if open_columns is None:
            open_columns = range(len(board))

        for i in open_columns:
            # Find the next empty cell index in the column
            index = next((j for j, cell in enumerate(board[i]) if cell == 0), None)
            
            # If the column is full, skip this column
            if index is None:
                continue

            # Make a deep copy of the board and place the piece
            new_board = deepcopy(board)
            new_board[i][index] = piece
            moves.append(new_board)
            
            # If there's room for more moves in this column, record it in options
            if index < len(board[i]) - 1:  # There is space above
                options[i] = index + 1

        # Print all possible moves for debugging
        for move in moves:
            print(connect4(board=move))
        
        print("Options:", options)

    def check_win(self, board=None, color=None): # Check 
        board = self.board if not board else board
        color = -1 * self.check_move_color() if not color else color # use last player who moved if no color provided

        pass # looking to use recursive function

    def check_win_probability(self, coordinates, board=None, piece_heat=None,
                              consecutive={"horiz": 0, "vert": 0, "TL_BR" : 0, "TR_BL": 0},
                              origin=None, wrap_around=False, negative_coords=False):
        
        board = self.board if not board else board
        # piece_heat: dict with horiz, vert, TL_BR and TR_BL as keys, integer values 0-4
        # consecutive: dict with horiz, vert, TL_BR and TR_BL as keys, integer values 0-3
        x, y = coordinates
        origin = (x, y+1) if not origin else origin  # limits search area to 7 instead of 8 to not retread

        main_piece = board[x][y]
        if piece_heat is None:
            piece_heat = {}
            for key, value in self.gen_heat.items():
                piece_heat[key] = value[x][y]

        test_coords = {}
        total_heat = {}
        vert_spots = {}
        horiz_spots = {}
        TL_BR_spots = {}
        TR_BL_spots = {}
        piece_grid = []
        print(f"Piece: {main_piece}")
        for i in range(3):
            coord_x = x + 1 - i
            for j in range(3):
                coord_y = y + 1 - j
                if ((coord_x >= 0) and (coord_y >= 0)) or (wrap_around == True):
                    piece = board[coord_x][coord_y]
                    test_coords[(coord_x, coord_y)] = board[coord_x][coord_y]
                    if (coord_x == origin[0] and coord_y == origin[1]):
                        print(f"Skipping origin piece at: {coord_x, coord_y}")
                        continue
                    if (i == j == 1):
                        print(f"Skipping central piece at: {coord_x, coord_y}")
                        continue  # central piece or piece of origin
                    if piece == main_piece:  # if it matches pattern
                        total_heat[(coord_x, coord_y)] = 0
                        
                        mini_classes= {}
                        max_mini_heat_order = []
                        if i == 1:  # Columns
                            heat = self.gen_heat["vert"][coord_x][coord_y] # get general heat of location
                            heat = heat * (consecutive["vert"]+1) # multiply weight by 1-4 depending on consecutive pieces in a given direction
                            if (heat > 0) or negative_coords:
                                if not(heat in mini_classes.keys()):
                                    mini_classes[heat] = ["vert"]
                                else:
                                    mini_classes[heat].append("vert")
                                if not heat in max_mini_heat_order:
                                    max_mini_heat_order.append(heat)
                                vert_spots[(coord_x, coord_y)] = heat
                                total_heat[(coord_x, coord_y)] += heat
                        if j == 1:  # Rows
                            heat = self.gen_heat["horiz"][coord_x][coord_y]
                            heat = heat * (consecutive["horiz"]+1) # multiply weight by 1-4 depending on consecutive pieces in a given direction
                            if (heat > 0) or negative_coords:
                                horiz_spots[(coord_x, coord_y)] = heat
                                total_heat[(coord_x, coord_y)] += heat
                        if i == j:  # down-right
                            heat = self.gen_heat["TL_BR"][coord_x][coord_y]
                            heat = heat * (consecutive["TL_BR"]+1) # multiply weight by 1-4 depending on consecutive pieces in a given direction
                            if (heat > 0) or negative_coords:
                                TL_BR_spots[(coord_x, coord_y)] = heat
                                total_heat[(coord_x, coord_y)] += heat
                        else:  # down-left
                            heat = self.gen_heat["TR_BL"][coord_x][coord_y]
                            heat = heat * (consecutive["TR_BL"]+1) # multiply weight by 1-4 depending on consecutive pieces in a given direction
                            if (heat > 0) or negative_coords:
                                TR_BL_spots[(coord_x, coord_y)] = heat
                                total_heat[(coord_x, coord_y)] += heat
                        print(f"Total Heat at {coord_x, coord_y}: {total_heat[(coord_x, coord_y)]}")
                            
                        

        print("For piece at ")
        print(test_coords)

        print("Vertical Options")
        print(vert_spots)
        print("Horizontal Options")
        print(horiz_spots)
        print("TL-BR Options")
        print(TL_BR_spots)
        print("TR-BL Options")
        print(TR_BL_spots)

        
        print("Total Heat")
        print(total_heat)

        max_heat_order = []
        classes = {} # classes of equivalent heats
        
        for coords, heat in total_heat.items():
            if len(max_heat_order) > 0 : # if max_heat_order has elements
                if heat > max_heat_order[-1]: # if the heat is greater than the current max heat
                    max_heat_order.append(heat) # update max_heat order
            else:# if max_heat_order doesnt have elements
                max_heat_order.append(heat) # start max_heat order
            if not(heat in classes.keys()):
                classes[heat] = [] # initialize this heat
                print(heat, classes[heat])
            print(heat, classes[heat])

            mini_classes= {}
            max_mini_heat_order = []
            vert_heat = 0 if not( coords in vert_spots.keys()) else vert_spots[coords]
            horiz_heat = 0 if not( coords in horiz_spots.keys()) else horiz_spots[coords]
            TL_BR_heat = 0 if not( coords in TL_BR_spots.keys()) else TL_BR_spots[coords]
            TR_BL_heat = 0 if not( coords in TR_BL_spots.keys()) else TR_BL_spots[coords] # replace with similar ranking system to total heat

            classes[heat].append((coords, vert_heat, horiz_heat, TL_BR_heat, TR_BL_heat ))

        print("Heat Classes")
        print(classes)
        print("Highest heat")
        print(max_heat_order[-1])


    def generate_matrix(self, height=None, width=None, default_value=0):
        if height == None or width == None:
            board = self.board
            width = len(board)
            height = len(board[0])
        return [[default_value for _ in range(width)] for _ in range(height)]

    def print_heatmap(self, matrix):
        # Find min and max values in the matrix
        min_val = min(min(row) for row in matrix)
        max_val = max(max(row) for row in matrix)
        range_val = max_val - min_val if max_val != min_val else 1  # Avoid division by zero

        # Color function that interpolates between red, yellow, and green based on value
        def get_color(value):
            # Normalize the value between 0 and 1
            normalized = (value - min_val) / range_val
            if normalized < 0.5:  # From red to yellow
                red = 255
                green = int(510 * normalized)  # Scale green from 0 to 255
                blue = 0
            else:  # From yellow to green
                red = int(510 * (1 - normalized))  # Scale red from 255 to 0
                green = 255
                blue = 0
            return f"\033[38;2;{red};{green};{blue}m"

        # Print each row with the color applied
        for row in matrix:
            for value in row:
                color = get_color(value)
                print(f"{color}{value:5}\033[0m", end=" ")
            print()  # Newline after each row

    def calculate_generic_heat_map(self, board=None, debug=False):
        board = self.board if not board else board
        width = len(board)
        height = len(board[0])

        # Initialize heatmap
        heatmap = self.generate_matrix(height, width, 0)
        heatmap1 = self.generate_matrix(height, width, 0)
        heatmap2 = self.generate_matrix(height, width, 0)
        heatmap3 = self.generate_matrix(height, width, 0)
        heatmap4 = self.generate_matrix(height, width, 0)

        # Horizontal lines
        for row in range(height):
            for col in range(width - 3):
                for i in range(4):
                    heatmap[row][col + i] += 1
                    heatmap4[row][col + i] += 1

        # Vertical lines
        for col in range(width):
            for row in range(height - 3):
                for i in range(4):
                    heatmap1[row + i][col] += 1
                    heatmap4[row + i][col] += 1

        # Diagonal down-right lines
        for row in range(height - 3):
            for col in range(width - 3):
                for i in range(4):
                    heatmap2[row + i][col + i] += 1
                    heatmap4[row + i][col + i] += 1

        # Diagonal up-right lines
        for row in range(3, height):
            for col in range(width - 3):
                for i in range(4):
                    heatmap3[row - i][col + i] += 1
                    heatmap4[row - i][col + i] += 1

        if debug:
            self.print_heatmap(heatmap)
            self.print_heatmap(heatmap1)
            self.print_heatmap(heatmap2)
            self.print_heatmap(heatmap3)
            self.print_heatmap(heatmap4)

        return {"horiz": heatmap, "vert": heatmap1, "TL_BR": heatmap2, "TR_BL": heatmap3, "total": heatmap4}


# assume red goes first

example_board = [
    [-1,1,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]
]

example_board_2 = [
    [0,0,-1,1],[0,0,0,0],[0,3,0,0],[0,0,0,0]
]

example_board_3 = [
    [1,-1,1,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]
]

conn1 = connect4(board=example_board)
print(conn1)

conn1.find_move_options()
conn1.check_win_probability((1,1))