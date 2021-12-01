#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
import copy
import math
import array
import competitive_sudoku.sudokuai
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove, print_board


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

        self.top_move = Move(0,0,0)
        self.max_value = 0
        self.max_value_start = 0



    def compute_best_move(self, game_state: GameState) -> None:

        # Get the standard needed variables
        N = game_state.board.N  # depth of matrix
        n = game_state.board.n  # number of rows in a block
        m = game_state.board.m  # number of columns in a block
        player1 = True            # This keeps track of whether we are player 1 or player 2



        open_squares_init = [(i, j) for i in range(N) for j in range(N) if game_state.initial_board.get(i, j) == SudokuBoard.empty]
        if len(game_state.moves) % 2 == 1:
            player1 = False            # Change our player number to 2 if we are player two

        def convert_to_matrix(board: SudokuBoard):
            """
            @param board: A sudoku board.
            @Return: a 2D array of the given board
            """
            matrix = [board.squares[i:i+N] for i in range(0, len(board.squares), N)]
            return matrix

        def possible(board: SudokuBoard):
            """
            @param board: A sudoku board.
            @Return: an array with all possible/legal moves in the Move format (x-coord, y-coord, value)
            """

            all_moves = []              # this will contain all the moves in the end
            # Make a list of all the squares that have not yet been filled in
            open_squares = [(i, j) for i in range(N) for j in range(N) if
                            board.get(i, j) == SudokuBoard.empty]
            for coords in open_squares:  # loop over all empty squares

                # calculate sub-squares and prepare list of possible values
                values_left = list(range(1, N+1))        # This list wil eventually contain all the values possible on coordinate (i,j)
                (p, q) = (int(math.ceil((coords[0] + 1) / n) * n)-1, int(math.ceil((coords[1] + 1) / m) * m)-1)   # calculates the highest coordinates in the sub-square
                (r, s) = (p-(n-1), q-(m-1))                                                          # calculates the lowest coordinates in the sub-square

                # remove all values that already exist on the same row/column/box as coords from the possible value list for that coord.
                for i in range(N):
                    if board.get(coords[0], i) in values_left:
                        values_left.remove(board.get(coords[0], i))
                    if board.get(i, coords[1]) in values_left:
                        values_left.remove(board.get(i, coords[1]))
                for x in range(r, p+1):
                    for y in range(s, q+1):
                        if board.get(x, y) in values_left:
                            values_left.remove(board.get(x, y))

                for value in values_left:
                    all_moves.append(Move(coords[0], coords[1], value))

            # We input all moves and then check the oracle to see which ones are illegal
            for move in all_moves:
                if move in game_state.taboo_moves:
                    all_moves.remove(move)

            return all_moves

        # This part of the code is unused and obsolete!!!!!!!!
        def evaluate_board(board: SudokuBoard, move: Move):
            """
            @param move: The move considered on the board
            @param board: A sudoku board.
            @Return: an integer with a numeric value. Higher = better board state
            """
            move_check = True     # if true, valid move. false = not valid move
            matrix = convert_to_matrix(board)
            row_filled = column_filled = box_filled = 0

            # These loops increase the evaluation score for each row/column that has one place left to fill in (it can increase our score)
            # This loop checks whether there is another 0 on the same row and column, if so switches state to false
            for iterator in range(N):
                if matrix[move.i][iterator] == 0:
                    row_filled += 1
                if matrix[iterator][move.j] == 0:
                    column_filled += 1

            # create all the sub_squares
            # sub_squares = [[matrix[j][i] for j in range(x, x + m) for i in range(y, y + n)] for x in range(0, N, m)for y in range(0, N, n)]

            # Calculate in which quadrant the given move falls.
            (p, q) = (int(math.ceil((move.i + 1) / n) * n) - 1, int(math.ceil((move.j + 1) / m) * m) - 1)  # calculates the highest coordinates in the sub-square
            (r, s) = (p - (n - 1), q - (m - 1))  # calculates the lowest coordinates in the sub-square

            # For the given quadrant, check whether any of the squares are filled with zero, if so switch to false
            for x in range(r, p + 1):
                for y in range(s, q + 1):
                    if board.get(x, y) == 0:
                        box_filled +=1
            if row_filled == 1 or column_filled == 1 or box_filled ==1:
                move_check = False

            return move_check

        # This evaluation function uses the score of the board as the eventual evaluation function
        def score_eval(board: SudokuBoard, move: Move):
            """
             @param move: A move
             @param board: A sudoku board.
             @Return: Return the value in points that the move has if it would be played on the board
             """

            matrix = convert_to_matrix(board)               # Quick conversion to do simple calculations
            row_filled = column_filled = box_filled = True  # These variables are false when there is a 0 in their area on the board

            # This loop checks whether there is another 0 on the same row and column, if so switches state to false
            for iterator in range(N):
                if matrix[move.i][iterator] == 0:
                    row_filled = False
                if matrix[iterator][move.j] == 0:
                    column_filled = False

            # Calculate in which quadrant the given move falls.
            (p, q) = (int(math.ceil((move.i + 1) / n) * n) - 1, int(math.ceil((move.j + 1) / m) * m) - 1)  # calculates the highest coordinates in the sub-square
            (r, s) = (p - (n - 1), q - (m - 1))  # calculates the lowest coordinates in the sub-square

            # For the given quadrant, check whether any of the squares are filled with zero, if so switch to false
            for x in range(r, p + 1):
                for y in range(s, q + 1):
                    if board.get(x, y) == 0:
                        box_filled = False

            # Increase the score by the point value depending on how many areas inputting the move would close off
            boolean_list = [row_filled, column_filled, box_filled]
            true_values = sum(boolean_list)
            if true_values == 1:
                score = 1
            elif true_values == 2:
                score = 3
            elif true_values == 3:
                score = 7
            else:
                score = 0

            return score


        def minimax(board: SudokuBoard, depth, is_maximising_player):
            """
            @param board: A sudoku board.
            @param depth: The corresponding depth within the tree.
            @param is_maximising_player: True/False indicator for min/max search.
            @Return: return the best possible next move according to the minimax
            """

            all_moves_list = possible(game_state2.board)                      # Check all moves on the copied board


            if depth == max_depth or len(all_moves_list) == 0:    # Checks whether we are in a leaf node or on the last possible move
                return game_state2.scores[0]-game_state2.scores[1]

            if is_maximising_player:                              # Check whether we are the maximising player
                value = -math.inf

                for move in all_moves_list:


                    # This chunk places the move on a copy of the board, evaluates it and updates the copied score
                    game_state2.board.put(move.i, move.j, move.value)
                    calculated_score = score_eval(game_state2.board, move)
                    game_state2.scores[0] += calculated_score


                    # print(game_state2.scores)
                    value = max(value, minimax(game_state2.board, depth + 1, False))      # Here we go into recursion

                    # After the recursion we remove the move and also re-calculate the score
                    game_state2.board.put(move.i, move.j, 0)
                    game_state2.scores[0] = game_state2.scores[0]-calculated_score


                    if depth == 0 and move not in game_state.taboo_moves and value > self.max_value_start:          # if depth == 0 and also not a taboo_move, propose it
                        if value > self.max_value:
                            self.max_value = value
                            # self.propose_move(move)
                            self.top_move = Move(move.i,move.j,move.value)
                        #TODO, propose een move in de for loop helemaal beneden
                    elif depth == 0 and move not in game_state.taboo_moves and value == self.max_value == self.max_value_start:
                        # self.max_value = value
                        # print(move)
                        # self.propose_move(move)
                        self.top_move = Move(move.i, move.j, move.value)

                return value                                      # Return the value (Not sure if this is necessary)

            else:                                                 # If we are not the maximizing player we end up here
                value = math.inf                                  # Declare highest possible number to compare negative against

                for move in all_moves_list:                       # iterate over all the enemies moves

                    # Once again, place the move on the board and update the score
                    game_state2.board.put(move.i, move.j, move.value)
                    calculated_score2 = score_eval(game_state2.board, move)
                    game_state2.scores[1] += calculated_score2
                    # print("Move: ", move, " Depth: ", depth)

                    value = min(value, minimax(game_state2.board, depth + 1, True))  # Another recursive loop

                    game_state2.board.put(move.i, move.j, 0)                         # Revert the played move and revert the scores to how it was
                    game_state2.scores[1] = game_state2.scores[1] - calculated_score2

                return value


        def minimax_alpha_beta(board: SudokuBoard, depth, alpha, beta, is_maximising_player):
            """
            @param board: A sudoku board.
            @param depth: The corresponding depth within the tree.
            @param is_maximising_player: True/False indicator for min/max search.
            @Return: return the best possible next move according to the minimax
            """

            all_moves_list = possible(game_state2.board)                      # Check all moves on the copied board


            if depth == max_depth or len(all_moves_list) == 0:    # Checks whether we are in a leaf node or on the last possible move
                return game_state2.scores[0]-game_state2.scores[1]

            if is_maximising_player:                              # Check whether we are the maximising player
                max_evaluation = -math.inf

                for move in all_moves_list:


                    # This chunk places the move on a copy of the board, evaluates it and updates the copied score
                    game_state2.board.put(move.i, move.j, move.value)
                    calculated_score = score_eval(game_state2.board, move)
                    game_state2.scores[0] += calculated_score


                    # print(game_state2.scores)
                    value = minimax_alpha_beta(game_state2.board, depth + 1, alpha, beta, False)    # Here we go into recursion

                    max_evaluation = max(value, max_evaluation)


                    # After the recursion we remove the move and also re-calculate the score
                    game_state2.board.put(move.i, move.j, 0)
                    game_state2.scores[0] = game_state2.scores[0]-calculated_score

                    alpha = max(alpha, value)

                    if beta <= alpha:
                        break

                    if depth == 0 and move not in game_state.taboo_moves and max_evaluation > self.max_value_start:          # if depth == 0 and also not a taboo_move, propose it
                        if max_evaluation > self.max_value:
                            self.max_value = max_evaluation
                            # self.propose_move(move)
                            self.top_move = Move(move.i,move.j,move.value)
                        #TODO, propose een move in de for loop helemaal beneden
                    elif depth == 0 and move not in game_state.taboo_moves and max_evaluation == self.max_value == self.max_value_start:
                        # self.max_value = value
                        # print(move)
                        # self.propose_move(move)
                        self.top_move = Move(move.i, move.j, move.value)

                return max_evaluation                                      # Return the value (Not sure if this is necessary)

            else:                                                 # If we are not the maximizing player we end up here
                min_evaluation = math.inf                                  # Declare highest possible number to compare negative against

                for move in all_moves_list:                       # iterate over all the enemies moves

                    # Once again, place the move on the board and update the score
                    game_state2.board.put(move.i, move.j, move.value)
                    calculated_score2 = score_eval(game_state2.board, move)
                    game_state2.scores[1] += calculated_score2
                    # print("Move: ", move, " Depth: ", depth)

                    value = minimax_alpha_beta(game_state2.board, alpha, beta, depth + 1, True)  # Another recursive loop
                    min_evaluation = max(value, min_evaluation)

                    game_state2.board.put(move.i, move.j, 0)                         # Revert the played move and revert the scores to how it was
                    game_state2.scores[1] = game_state2.scores[1] - calculated_score2

                    beta = min(beta, value)
                    if beta <= alpha:
                        break

                return min_evaluation

        max_depth = 0
        game_state2 = copy.deepcopy(game_state)

        self.max_value = game_state2.scores[0] - game_state2.scores[1]
        self.max_value_start = game_state2.scores[0] - game_state2.scores[1]


        # # This is the iterative deepening code, it's very crude but it could be improved (for now always start at 0)


        # for i in range(0, 7):
        #     max_depth = i                                         # Update the max depth
        #
        #
        #     #all_moves = possible(game_state.board)
        #
        #     # if len(all_moves) > 30:
        #     #     self.propose_move(random.choice(all_moves))
        #     # else:
        #
        #     minimax(game_state.board, 0, True)
        #     #minimax_alpha_beta(game_state.board, 0, -math.inf, math.inf, True)      # call the minmax function for the given max_depth
        #
        #     self.propose_move((self.top_move))


        all_moves = possible(game_state.board)
        print(len(all_moves))

        if len(all_moves) > 40:
            while True:
                considered_move = random.choice(all_moves)
                game_state2.board.put(considered_move.i, considered_move.j, considered_move.value)
                if evaluate_board(game_state2.board, considered_move) and considered_move not in game_state.taboo_moves:
                        self.propose_move(considered_move)
                        game_state2.board.put(considered_move.i, considered_move.j, 0)
                        break

        # This is the iterative deepening code, it's very crude but it could be improved (for now always start at 0)
        else:
            max_depth = 0
            if not player1:
                game_state2.scores[0], game_state2.scores[1] = game_state2.scores[1], game_state2.scores[0]
                self.max_value = game_state2.scores[0] - game_state2.scores[1]
                self.max_value_start = game_state2.scores[0] - game_state2.scores[1]


            for i in range(0, 8):
                max_depth = i                                         # Update the max depth
                minimax(game_state.board, 0, True)      # call the minmax function for the given max_depth
                self.propose_move(self.top_move)