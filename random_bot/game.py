from constants import *
import math

def isWin(board, neighbours, turn):
        board_size = int(math.sqrt(len(board)))
        seen = set()

        def dfs(i, color, level=0):
            """Oopsie poopsie! I made a fucky wucky! This code is super-duper slow! UwU7

            Args:
                i (int): The current location of the depth-first search
                color (int): The current color of the dfs.
            """
            is_right_column = (i + 1) % board_size == 0
            is_bottom_row = i >= board_size * (board_size - 1)

            if color == WHITE and is_right_column:
                return True
            elif color == BLACK and is_bottom_row:
                return True

            # Label hexagon as 'visited' so we don't get infinite recusion
            seen.add(i)
            for neighbour in neighbours[i]:
                if (
                    neighbour not in seen
                    and board[neighbour] == color
                    and dfs(neighbour, color, level=level + 1)
                ):
                    return True

            # Remove hexagon so we can examine it again next time (hint:is this needed?)
            seen.remove(i)
            return False

        # Iterate over all starting spaces for black & white, performing dfs on empty
        # spaces (hint: this leads to repeated computation!)
        for i in range(0, board_size):
            if board[i] == BLACK and dfs(i, BLACK):
                return (1 if turn == BLACK else -1)

        for i in range(0, len(board), board_size):
            if board[i] == WHITE and dfs(i, WHITE):
                return (1 if turn == WHITE else -1)

        return 0