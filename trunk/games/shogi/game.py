import random

class Game(object):
    def __init__(self):
        player1 = Player(self, "Mr. Miyamoto", True)
        player2 = Player(self, "Tom", False)
        self.players = [player1, player2]
        self.current_player = 0
        self.winner = None
        self.setup()

    def clone(self):
        g = Game()
        g.current_player = self.current_player
        g.winner = self.winner
        g.board = self.board.clone(self.players)
        return g
        
    def setup(self):
        self.board = Board()
        for p in self.players:
            self.setup_player(p)
        
    def setup_player(self, player):
        if player.top:
            reflect = 1
            adjust_x = 0
            adjust_y = 0
        else:
            reflect = -1
            adjust_x = 8
            adjust_y = 8
            
        pieces = [
            (King, 4, 0),
            (Rook, 7, 1),
            (Bishop, 1, 1),
            (Gold_General, 3, 0),
            (Gold_General, 5, 0),
            (Silver_General, 2, 0),
            (Silver_General, 6, 0),
            (Knight, 1, 0),
            (Knight, 7, 0),
            (Lance, 0, 0),
            (Lance, 8, 0),
            (Pawn, 0, 2),
            (Pawn, 1, 2),
            (Pawn, 2, 2),
            (Pawn, 3, 2),
            (Pawn, 4, 2),
            (Pawn, 5, 2),
            (Pawn, 6, 2),
            (Pawn, 7, 2),
            (Pawn, 8, 2),
        ]
        
        def place_piece(klass, x, y):
            piece = klass(self.board, player, x * reflect + adjust_x, y * reflect + adjust_y)
        
        for k, x, y in pieces:
            place_piece(k, x, y)
    
    def get_current_player(self):
        return self.players[self.current_player]
        
        
class Board(object):
    def __init__(self):
        self.width = 9
        self.height = 9
        self.cells = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(None)
            self.cells.append(row)
    
    def clone(self, players):
        b = Board()
        for i in range(self.height):
            for j in range(self.width):
                if self.cells[i][j] is not None:
                    b.cells[i][j] = self.cells[i][j].clone(b, players)
                else:
                    b.cells[i][j] = None
        return b
    
    def set_cell(self, x, y, piece):
        self.cells[y][x] = piece
    
    def __str__(self):
        s = ""
        for i in range(self.height):
            for j in range(self.width):
                piece = self.cells[i][j]
                if piece is None:
                    s = s + "."
                else:
                    if piece.player.top:
                        s = s + str(piece)
                    else:
                        s = s + str(piece).lower()
            s = s + "\n"
        return s

    def apply_move(self, move):
        old_x = move.piece.x
        old_y = move.piece.y
        new_x = old_x + move.dx
        new_y = old_y + move.dy
        taken = self.cells[new_y][new_x]
        won = False
        if taken is not None:
            won = taken.die()
        self.set_cell(old_x, old_y, None)
        move.piece.change_position(new_x, new_y)
        self.set_cell(new_x, new_y, move.piece)
        return won

    def is_move_outside(self, move):
        old_x = move.piece.x
        old_y = move.piece.y
        new_x = old_x + move.dx
        new_y = old_y + move.dy
        
        if new_x < 0:
            return True
        if new_y < 0:
            return True
        if new_x >= self.width:
            return True
        if new_y >= self.height:
            return True
        
        return False
    
    def is_move_blocked(self, move):
        old_x = move.piece.x
        old_y = move.piece.y
        new_x = old_x + move.dx
        new_y = old_y + move.dy
        
        p = self.cells[new_y][new_x]
        if p is None:
            return False
        
        if move.piece.player == p.player:
            return True
    
        return False
    
    def is_move_capture(self, move):
        old_x = move.piece.x
        old_y = move.piece.y
        new_x = old_x + move.dx
        new_y = old_y + move.dy
        
        p = self.cells[new_y][new_x]
        if p is None:
            return False
        
        if move.piece.player != p.player:
            return True
    
        return False
    
    def get_pieces(self):
        pieces = []
        for row in self.cells:
            for cell in row:
                if cell is not None:
                    pieces.append(cell)
        return pieces
    
class Piece(object):
    def __init__(self, board, player, x, y):
        self.board = board
        self.x = x
        self.y = y
        self.board.set_cell(x, y, self)
        self.player = player
        self.dead = False

    def clone(self, board, players):
        if players[0].name == self.player.name:
            player = players[0]
        else:
            player = players[1]
        p = self.__class__(board, player, self.x, self.y)
        return p

    def die(self):
        self.dead = True
        return False

    def change_position(self, x, y):
        self.x = x
        self.y = y
    
    def get_moves(self):
        moves = self.get_raw_moves()
        
        def is_ok(move):
            return not self.board.is_move_outside(move) and not self.board.is_move_blocked(move)
        
        return filter(is_ok, moves)
            
        
class King(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'King'

    def __str__(self):
        return "K"
        
    def die(self):
        Piece.die(self)
        return True
        
    def get_raw_moves(self):
        l = [(0,1), (1,0), (0,-1), (-1, 0), (-1, 1), (1, -1), (-1, -1), (1, 1)]
        moves = []
        for dx, dy in l:
            m = Move(self, dx, dy)
            moves.append(m)
        return moves
        
class Rook(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Rook'

    def __str__(self):
        return "R"
        
    def get_raw_moves(self):
        l = [(-1, 0), (0, -1), (0, 1), (1, 0)]
        
        def is_ok(move):
            return not self.board.is_move_outside(move) and not self.board.is_move_blocked(move) and not self.board.is_move_capture(move)
        
        moves = []
        for dx, dy in l:
            i = 1
            while True:
                m = Move(self, dx*i, dy*i)
                moves.append(m)
                if not is_ok(m):
                    break
                i = i + 1
        return moves
        
class Bishop(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Bishop'

    def __str__(self):
        return "B"
        
    def get_raw_moves(self):
        l = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        def is_ok(move):
            return not self.board.is_move_outside(move) and not self.board.is_move_blocked(move) and not self.board.is_move_capture(move)
        
        moves = []
        for dx, dy in l:
            i = 1
            while True:
                m = Move(self, dx*i, dy*i)
                moves.append(m)
                if not is_ok(m):
                    break
                i = i + 1
        return moves
    
        
class Gold_General(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Gold General'

    def __str__(self):
        return "G"
        
    def get_raw_moves(self):
        if self.player.top:
            dy = 1
        else:
            dy = -1
        l = [(0,1), (0,-1), (-1,0), (1,0), (-1,dy), (1,dy)]
        moves = []
        for dx, dy in l:
            m = Move(self, dx, dy)
            moves.append(m)
        return moves

class Silver_General(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Silver General'

    def __str__(self):
        return "S"
        
    def get_raw_moves(self):
        if self.player.top:
            dy = 1
        else:
            dy = -1
        l = [(-1,1), (1,1), (-1,-1), (1,-1), (0,dy)]
        moves = []
        for dx, dy in l:
            m = Move(self, dx, dy)
            moves.append(m)
        return moves
        
class Knight(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Knight'

    def __str__(self):
        return "N"
        
    def get_raw_moves(self):
        if self.player.top:
            dy = 2
        else:
            dy = -2
        l = [(1,dy), (-1,dy)]
        moves = []
        for dx, dy in l:
            m = Move(self, dx, dy)
            moves.append(m)
        return moves
        
class Lance(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Lance'

    def __str__(self):
        return "L"
            
    def get_raw_moves(self):
        if self.player.top:
            dy = 1
        else:
            dy = -1
        l = [(0,dy)]
        
        def is_ok(move):
            return not self.board.is_move_outside(move) and not self.board.is_move_blocked(move) and not self.board.is_move_capture(move)
        
        moves = []
        for dx, dy in l:
            i = 1
            while True:
                m = Move(self, dx*i, dy*i)
                moves.append(m)
                if not is_ok(m):
                    break
                i = i + 1
        return moves

class Pawn(Piece):
    def __init__(self, board, player, x, y):
        Piece.__init__(self, board, player, x, y)
        self.name = 'Pawn'

    def __str__(self):
        return "P"
    
    def get_raw_moves(self):
        if self.player.top:
            dy = 1
        else:
            dy = -1
        l = [(0,dy)]
        moves = []
        for dx, dy in l:
            m = Move(self, dx, dy)
            moves.append(m)
        return moves
        
class Player(object):
    def __init__(self, game, name, top):
        self.name = name
        self.game = game
        self.top = top
    
    def clone(self, game):
        if game.players[0].name == self.name:
            return game.players[0]
        else:
            return game.players[1]
        
    def __str__(self):
        return self.name
    
    def get_pieces(self):
        
        def is_mine(p):
            return p.player.name == self.name
        
        pieces = filter(is_mine, self.game.board.get_pieces())
        return pieces

    def get_moves(self):
        moves = []
        if self.game.winner is not None:
            return moves
        for piece in self.get_pieces():
            moves = moves + piece.get_moves()
        return moves

    def do_move(self, move):
        won = self.game.board.apply_move(move)
        self.game.current_player = 1 - self.game.current_player
        if won:
            self.game.winner = self
        return won

class Move(object):
    def __init__(self, piece, dx, dy):
        self.piece = piece
        self.dx = dx
        self.dy = dy
        
    def clone(self, game):
        px = self.piece.x
        py = self.piece.y
        p = game.board.cells[py][px]
        m = Move(p, self.dx, self.dy)
        return m
        
    def __str__(self):
        return "%s:%d,%d" % (self.piece, self.dx, self.dy)
                
        
def test():
    g = Game()
    print g.board
    for i in xrange(10):
        p = g.get_current_player()
        print "Player:", p
        moves = p.get_moves()
        if moves == []:
            break
        m = moves[random.randrange(0, len(moves))]
        p.do_move(m)
        print g.board

