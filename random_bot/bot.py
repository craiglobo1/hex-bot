from constants import EMPTY, WHITE, BLACK
from random import choice, seed
import math
from game import *
# from copy import deepcopy
seed(42)  # Get same results temporarily

# Note: WHITE goes left->right, BLACK goes top->bottom

class Node:
    def __init__(self, prior, turn, state) -> None:
        self.prior  = prior
        self.turn   = turn
        self.state  = state
        self.children = {}
        self.value = 0
        self.vists = 0

    def expand(self, action_prob):
        for action, prob in enumerate(action_prob):
            if prob > 0:
                state_copy = [ val for val in self.state]
                state_copy[action] = self.turn
                self.children[action] = Node(prob, -1*self.turn, state_copy)
    
    def select_child(self):
        ucb = lambda child, parent : (child.prior * math.sqrt(parent.vists) / (child.vists + 1)) +  ((child.value/child.vists) if child.vists != 0 else 0)
        max_score = -1e9
        for action, child in self.children.items():
            score = ucb(self, child)
            if score > max_score:
                selected_action  = action
                selected_child  = child
                max_score = score
        
        return selected_action, selected_child


class RandomHexBot:
    def __init__(self, color, board_size=11):
        self.color = color
        self.opp = BLACK if color == WHITE else WHITE
        self.move_count = 0
        self.init_board(board_size)

        self.pub = {
            "init_board": self.init_board,
            "show_board": self.show_board,
            "make_move": self.make_move,
            "seto": self.seto,
            "sety": self.sety,
            "unset": self.unset,
            "check_win": self.check_win,
        }

        self.argnums = {
            "init_board": 1,
            "show_board": 0,
            "make_move": 0,
            "seto": 1,
            "sety": 1,
            "unset": 1,
            "check_win": 0,
        }

    def is_cmd(self, cmd):
        """Checks to see whether the command in 'cmd' conforms to the expected format

        Args:
            cmd (List[str]): A space-separated list of the commands given on the command line

        Returns:
            bool: True if the command exists and has the correct # of arguments, False otherwise
        """
        assert len(cmd)
        if cmd[0] not in self.pub:
            return False
        if len(cmd) - 1 != self.argnums[cmd[0]]:
            return False

        return True

    def run_command(self, cmd):
        """Executes the command contained within 'cmd' if it is applicable

        Args:
            cmd (List[str]): A space-separated list of the commands given on the command line
        """
        if len(cmd) > 1:
            self.pub[cmd[0]](cmd[1])
        else:
            self.pub[cmd[0]]()

    def init_board(self, board_size):
        """Tells the bot to reset the game to an empty board with a specified side length

        Args:
            board_size (int): The width & height of the hex game board to create
        """
        board_size = int(board_size)
        self.board_size = board_size
        self.board = [EMPTY for i in range(board_size**2)]
        self.move_count = 0

        self.init_neighbours()

    def show_board(self):
        """Prints the board to stdout. This is primarily used for
        testing purposes & when playing against a human opponent

        Returns:
            bool: True if the command exists and ran successfully, False otherwise
        """
        tile_chars = {
            EMPTY: ".",
            BLACK: "B",
            WHITE: "W",
        }

        chars = list(map(lambda x: tile_chars[x], self.board))

        for i in reversed(range(1, self.board_size+1)):  # Reverse to avoid shifting indicies
            chars.insert(i * self.board_size, "|")

        print("".join(chars))
        return

    def dummy_model_predict(self, state):

        policy_head = [  0.5 for _ in self.board]

        # mask policy with possible moves
        for i, cell in enumerate(state):
            if cell != EMPTY:
                policy_head[i] = 0
                
        value_head = 0.5

        return value_head, policy_head

    def make_move(self):
        """Generates the move. For this bot, the move is randomly selected from all empty positions."""
        empties = []
        for i, cell in enumerate(self.board):
            if cell == EMPTY:
                empties.append(i)

        root = Node(prior=0, turn=1, state=self.board)

        value, action_probs = self.dummy_model_predict(self.board)
        root.expand(action_probs)


        # simple function to turn board into a readble string
        cool_show = lambda x: ( "W" if x == WHITE else ( "B" if x == BLACK else "."))
        

        sim = 100
        for _ in range(sim):
            node = root
            search_path = [node]
            while len(node.children) > 0:
                action, node = node.select_child()
                search_path.append(node)
            
            # add if win or lose
            value = isWin(node.state, self.neighbours, node.turn)

            if value == 0:
                value, action_probs = self.dummy_model_predict(node.state)
                node.expand(action_probs)

            for node in search_path:
                node.value += value
                node.vists += 1

        

        # print([ (node.value, "".join(map(cool_show, node.state))) for node in root.children.values()])

        max_val = -1e9
        for action, node in root.children.items():
            if node.value > max_val:
                max_action = action
                max_val = node.value

        move = self.coord_to_move(pos := max_action)
        self.sety(move)
        print(move)
        return



    def seto(self, move):
        """Tells the bot about a move for the other bot

        Args:
            move (str): A human-readable position on which the opponent has just played
        """
        # TODO: Handle swap move. Logic moved to move_to_coord()
        coord = self.move_to_coord(move)
        if self.board[coord] == EMPTY:
            # TODO: Warn or not?
            #print("Trying to play on a non-empty square!")
            self.board[coord] = self.opp
            self.move_count += 1
        return

    def sety(self, move):
        """Set Your [tile]. Tells the bot to play a move for itself

        Args:
            move (str): A human-readable position on the board
        """
        coord = self.move_to_coord(move)
        if self.board[coord] != EMPTY:
            #print("Trying to play on a non-empty square!")
            return
        self.board[coord] = self.color
        self.move_count += 1
        return

    def unset(self, move):
        """Tells the bot to set a tile as unused

        Args:
            move (str): A human-readable position on the board
        Returns:
            bool: True if the move has been unmade, False otherwise
        """

        coord = self.move_to_coord(move)
        self.board[coord] = EMPTY
        return True

    def check_win(self):
        """Checks whether or not the game has come to a close.

        Returns:
            int: 1 if this bot has won, -1 if the opponent has won, and 0 otherwise. Note that draws
            are mathematically impossible in Hex.
        """
        print(isWin(self.board, self.neighbours, self.color))

    def init_neighbours(self):
        """Precalculates all neighbours for each cell"""
        self.neighbours = []

        offsets_normal = [-1, 1, -self.board_size, self.board_size, -self.board_size+1, self.board_size-1]
        offsets_left   = [    1, -self.board_size, self.board_size, -self.board_size+1                   ]
        offsets_right  = [-1,    -self.board_size, self.board_size,                     self.board_size-1]

        def legalize_offsets(cell, offsets):
            a = []
            for offset in offsets:
                if 0 <= cell + offset < self.board_size**2:
                    a.append(cell + offset)
            return a

        for cell in range(self.board_size**2):
            if (cell+1) % self.board_size == 0:
                offsets = offsets_right
            elif cell % self.board_size == 0:
                offsets = offsets_left
            else:
                offsets = offsets_normal

            self.neighbours.append(legalize_offsets(cell, offsets))
        return

    def coord_to_move(self, coord):
        """Converts an integer coordinate to a human-readable move

        Args:
            coord (int): A coordinate within self.board

        Returns:
            str: A human-readable version of coord
        Example:
            >>> assert coord_to_move(0) == "a1"
            >>> assert coord_to_move(self.board_size + 2) == "b3"
            >>> assert coord_to_move(22 * self.board_size + 11) == "w12"
        """
        letter = chr(coord // self.board_size + ord("a"))
        number = coord % self.board_size + 1

        return f'{letter}{number}'

    def move_to_coord(self, move):
        """Converts a human-readable move to a coordinate within self.board

        Args:
            move (str): A human-readable position on the board

        Returns:
            int: The integer coordinate of 'move', used to interact with the board

        Example:
            >>> assert move_to_coord("a1") == 0
            >>> assert move_to_coord("b3") == self.board_size + 2
            >>> assert move_to_coord("w12") == 22 * self.board_size + 11
        """
        # TODO: Handle swap move
        if move == "swap":
            self.swap_move()
            return

        assert len(move) >= 2, "Move must be a character-digit pair. Ex: a12"
        assert move[0].isalpha(), "First character must be a letter. Ex: a12"
        assert move[1:].isdigit(), "Digits must follow the first character. Ex: a12"
        assert (
            ord(move[0]) - ord("a") < self.board_size
        ), "The letter in 'move' must have value less than board size!"
        assert (
            0 < int(move[1:]) <= self.board_size
        ), "Integer part of move must be within range (0, board_size]!"

        column = int(move[1:]) - 1
        row = ord(move[0]) - ord("a")
        return row * self.board_size + column
