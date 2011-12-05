import sys
import random
import pygame


class Board(object):
    def __init__(self, size=10, num_nodes=100):
        self.size = size
        self.cells = []
        for i in range(size):
            row = [' ']*size
            self.cells.append(row)

        nodes = []
        x, y = random.randrange(size), random.randrange(size)
        self.cells[y][x] = 0
        nodes.append((x,y))
        num_nodes -= 1

        dirs = [(0,-1), (0,1), (-1,0), (1, 0)]
        tries_left = 100
        while num_nodes > 0:
            if tries_left <= 0:
                #print >>sys.stderr, "Ran out of tries!"
                break
            x1, y1 = random.choice(nodes)
            dx, dy = random.choice(dirs)
            i = 1
            while i < size:
                x2 = x1 + dx*i
                y2 = y1 + dy*i
                if not self.in_range(x2, y2):
                    break
                if self.cells[y2][x2] != ' ':
                    break
                i += 1
            i -= 1
            if i < 2:
                tries_left -= 1
                continue
            n = random.randrange(2,i+1)
            x2 = x1 + dx*n
            y2 = y1 + dy*n
            if x2 > 0 and type(self.cells[y2][x2-1]) is int:
                tries_left -= 1
                continue
            if y2 > 0 and type(self.cells[y2-1][x2]) is int:
                tries_left -= 1
                continue
            if x2 < self.size-1 and type(self.cells[y2][x2+1]) is int:
                tries_left -= 1
                continue
            if y2 < self.size-1 and type(self.cells[y2+1][x2]) is int:
                tries_left -= 1
                continue
            w = random.randrange(1,3)
            self.cells[y1][x1] += w
            if dy != 0:
                marker = '|'
            else:
                marker = '-'
            for i in range(1,n):
                x2 = x1 + dx*i
                y2 = y1 + dy*i
                self.cells[y2][x2] = marker
            x2 = x1 + dx*n
            y2 = y1 + dy*n
            self.cells[y2][x2] = w
            nodes.append((x2,y2))
            num_nodes -= 1
            tries_left = 100

    def unsolve(self):
        for r in self.cells:
            for i in range(len(r)):
                if r[i] == '-' or r[i] == '|':
                    r[i] = ' '
    
    def find_moves(self, x, y):
        if self.cells[y][x] != ' ':
            return []
        dirs = [(0,1), (1, 0)]
        moves = []
        for dx,dy in dirs:
            r = self.find_node(x, y, -dx, -dy)
            if r is None:
                continue
            x1,y1 = r
            
            r = self.find_node(x, y, dx, dy)
            if r is None:
                continue
            x2,y2 = r
            
            moves.append((x1,y1,x2,y2))
        
        return moves
    
    def find_node(self, x, y, dx, dy):
        #print 'searching from %d,%d on %d,%d' % (x,y, dx, dy)
        x += dx
        y += dy
        while self.in_range(x, y):
            if type(self.cells[y][x]) is int:
                #print 'found target at %d,%d' % (x,y)
                return x,y
            if self.cells[y][x] != ' ':
                #print 'was %s instead of blank at %d,%d' % (self.cells[y][x], x,y)
                return None
            x += dx
            y += dy
        
        #print 'out of range at %d,%d' % (x,y)
        return None
    
    def in_range(self, x, y):
        return x >= 0 and y >= 0 and x < self.size and y < self.size

    def __str__(self):
        rs = []
        rs.append('*' * (self.size*2 + 3))
        for r in self.cells:
            cs = []
            prev_c = None
            for c in r:
                if c == ' ':
                    cs.append('  ')
                elif type(c) is int:
                    if prev_c == '-':
                        cs.append('-%d' % c)
                    else:
                        cs.append(' %d' % c)
                elif c == '|':
                    cs.append(' |')
                elif c == '-':
                    cs.append('--')
                else:
                    cs.append(c+c)
                prev_c = c
            rs.append('*' + ''.join(cs) + ' *')
        rs.append('*' * (self.size*2 + 3))
        s = '\n'.join(rs)
        return s


class Window(object):
    
    TILE_WIDTH = 20
    TILE_HEIGHT = 20
    
    def __init__(self, board):
        self.board = board
        
        self.width = self.TILE_WIDTH * board.size
        self.height = self.TILE_HEIGHT * board.size
        
        self.display = pygame.display.set_mode((self.width, self.height))
        
        self.font = pygame.font.SysFont(None, 22)
        
        self.current_tile = None

    def draw_tile(self, row, col):
        x1 = col * self.TILE_WIDTH
        y1 = row * self.TILE_HEIGHT
        w = self.TILE_WIDTH
        h = self.TILE_HEIGHT
        
        if self.current_tile == (col, row):
            border_col = (50, 100, 50)
            fill_col = (100, 50, 100)
        else:
            border_col = (50, 50, 100)
            fill_col = (100, 100, 50)
        pygame.draw.rect(self.display, border_col, pygame.Rect(x1, y1, w, h), 1)
        pygame.draw.rect(self.display, fill_col, pygame.Rect(x1+1, y1+1, w-2, h-2))

        if type(self.board.cells[row][col]) is int:
            text = self.font.render("%d" % self.board.cells[row][col], False, (255,255,255))
            tx = x1 + w/2 - text.get_width()/2
            ty = y1 + h/2 - text.get_height()/2
            self.display.blit(text, (tx, ty + 2))
        elif self.board.cells[row][col] == '|':
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1+w/2, y1, 2, h))
        elif self.board.cells[row][col] == '-':
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1, y1+h/2, w, 2))
    
    def draw(self):
        for i in range(self.board.size):
            for j in range(self.board.size):
                self.draw_tile(i, j)
        
        for x1,y1,x2,y2 in self.moves:
            px = x1 * self.TILE_WIDTH
            py = y1 * self.TILE_HEIGHT
            w = (x2 - x1 + 1) * self.TILE_WIDTH
            h = (y2 - y1 + 1) * self.TILE_HEIGHT
            pygame.draw.rect(self.display, (255, 0, 0), pygame.Rect(px, py, w, h), 1)
    
    def update(self):
        self.draw()
        pygame.display.flip()


class Control(object):
    def __init__(self, board, window):
        self.board = board
        self.window = window
    
    def update(self):
        redraw = False
        if self.update_mouse():
            redraw = True
        
        return redraw

    def update_mouse(self):
        mx, my = pygame.mouse.get_pos()
        tx = mx/self.window.TILE_WIDTH
        ty = my/self.window.TILE_HEIGHT
        if not self.board.in_range(tx, ty):
            return False
        
        if self.window.current_tile == (tx, ty):
            return False
        
        self.window.current_tile = (tx, ty)
        self.window.moves = self.board.find_moves(tx, ty)
        
        return True
    
    def click(self, mx, my):
        if self.window.moves == []:
            return
        x1,y1,x2,y2 = self.window.moves[0]
        if x1 == x2:
            dx, dy = 0, 1
            k = y2-y1
            c = '|'
        else:
            dx, dy = 1, 0
            k = x2-x1
            c = '-'
        for i in range(1,k):
            self.board.cells[y1+i*dy][x1+i*dx] = c


def main(args=None):
    if args is None:
        args = sys.argv
    
    pygame.init()
    
    board = Board()
    board.unsolve()
    window = Window(board)
    control = Control(board, window)

    pygame.time.set_timer(pygame.USEREVENT+1, 500)
    
    while True:
        ev = pygame.event.wait()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                break
            elif ev.key == pygame.K_r:
                board = Board()
                board.unsolve()
                window = Window(board)
                control = Control(board, window)
        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            control.click(mx, my)
        elif ev.type == pygame.USEREVENT+1:
            pass
        
        if control.update() or ev.type == pygame.USEREVENT+1:
            window.update()
            #print >>sys.stderr, 'update'

    pygame.quit()


if __name__ == '__main__':
    main()
