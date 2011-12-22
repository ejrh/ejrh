import sys
import random
import pygame


class Board(object):
    """The board.  Records the size and shape of the board, and the state of
    the nodes and bridges on it.
    
    The board consists of a two-dimension array of cells.  The possible cell
    values are:
    
      * An integer X: the cell is a node, and needs X additional bridges to
        connect to it.
      * A character '|' 'H' '-' or '=': the cell has a single or double
        horizontal or vertical line drawn through it.
      * The character ' ': the cell is empty.
    
    As bridges or drawn or removed, node values are changed.  The board is
    solved when all nodes have value 0.
    """
    
    def __init__(self, size=25, num_nodes=250):
        """Create a board object of the given size and maximum number of nodes.
        
        A tree of nodes and edges will be randomly generated, up to the
        specified number of nodes (it's possible fewer nodes will appear).
        
        The generated board will have all edges intact at the end.  Starting
        a new game requires erasing the edges first with the unsolve
        method."""
        
        # Create a blank board
        self.size = size
        self.cells = []
        for i in range(size):
            row = [' ']*size
            self.cells.append(row)

        # A list of existing nodes, with a single seed node in it.
        nodes = []
        x, y = random.randrange(size), random.randrange(size)
        self.cells[y][x] = 0
        nodes.append((x,y))
        num_nodes -= 1

        dirs = [(0,-1), (0,1), (-1,0), (1, 0)]
        tries_left = 100
        while num_nodes > 0:
            # Give up after 100 tries -- it's too hard to add any more nodes.
            if tries_left <= 0:
                #print >>sys.stderr, "Ran out of tries!"
                break
            
            # Pick a random node to start from, and a random direction.
            x1, y1 = random.choice(nodes)
            dx, dy = random.choice(dirs)
            
            # Find the maximum empty extent in that direction.
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
            
            # If less than 2, there's no room for a bridge.
            if i < 2:
                tries_left -= 1
                continue
            
            # Pick a random spot in that extent.
            n = random.randrange(2,i+1)
            x2 = x1 + dx*n
            y2 = y1 + dy*n
            
            # If any of that spot's neighbours are nodes, then we can't put
            # a node there.
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
            
            # Randomly choose whether it's a single or double bridge.
            w = random.randrange(1,3)
            
            # Increment the starting node.
            self.cells[y1][x1] += w
            
            # Draw a bridge.
            if dy != 0:
                marker = '|'
            else:
                marker = '-'
            for i in range(1,n):
                x2 = x1 + dx*i
                y2 = y1 + dy*i
                self.cells[y2][x2] = marker
            
            # Create a new node in the chosen spot.
            x2 = x1 + dx*n
            y2 = y1 + dy*n
            self.cells[y2][x2] = w
            nodes.append((x2,y2))
            num_nodes -= 1
            
            # Reset tries_left for the next node to add.
            tries_left = 100

    def unsolve(self):
        """Unsolve a board by erasing the edges on it."""
        
        for r in self.cells:
            for i in range(len(r)):
                if r[i] == '-' or r[i] == '|':
                    r[i] = ' '
    
    def find_moves(self, x, y):
        """Find the possible moves in spot (x, y).  A move is a tuple
        (x1, y1, x2, y2) that represents adding, doubling, or erasing a
        bridge between those nodes.  This method returns a list of moves.
        In practice there are up to 2 possible moves (horizontal and vertical);
        the vertical move will be earlier in the list if present."""
        
        if type(self.cells[y][x]) is int:
            return []
        dirs = [(0,1), (1, 0)]
        moves = []
        for dx,dy in dirs:
            # Search down/right for a node.
            r = self.find_node(x, y, -dx, -dy)
            if r is None:
                continue
            x1,y1 = r
            
            # Search up/left for a node.
            r = self.find_node(x, y, dx, dy)
            if r is None:
                continue
            x2,y2 = r
            
            # If both found, add the move.
            moves.append((x1,y1,x2,y2))
        
        return moves
    
    def find_node(self, x, y, dx, dy):
        """Find a node starting from a spot, in a given direction.
        Returns the node's coordinates (x,y), or None if not found."""
        
        #print 'searching from %d,%d on %d,%d' % (x,y, dx, dy)
        x += dx
        y += dy
        if dy == 0:
            ignores = ['-', '=']
        else:
            ignores = ['|', 'H']
        while self.in_range(x, y):
            if type(self.cells[y][x]) is int:
                #print 'found target at %d,%d' % (x,y)
                return x,y
            if self.cells[y][x] != ' ' and self.cells[y][x] not in ignores:
                #print 'was %s instead of blank at %d,%d' % (self.cells[y][x], x,y)
                return None
            x += dx
            y += dy
        
        #print 'out of range at %d,%d' % (x,y)
        return None
    
    def in_range(self, x, y):
        """Is the coordinate (x,y) on the board?"""
        return x >= 0 and y >= 0 and x < self.size and y < self.size
    
    def draw_line(self, x1, y1, x2, y2, thickness):
        """Draw a bridge between two nodes, of the given thickness.
        If the thickness is 0, a bridge will be erased.  1 and 2 correspond
        to single and double bridges.  The nodes must be orthogonally
        positioned.
        
        Node values will be incremented/decremented according
        to the bridge drawn, assuming that the existing bridge is 1 less.  I.e.
        a non-existent bridge is made single, a single bridge is doubled, and
        a double bridge is removed.
        """
        if x1 == x2:
            dx, dy = 0, 1
            k = y2-y1
            if thickness == 0:
                inc = 2
                c = ' '
            elif thickness == 1:
                inc = -1
                c = '|'
            else:
                inc = -1
                c = 'H'
        else:
            dx, dy = 1, 0
            k = x2-x1
            if thickness == 0:
                inc = 2
                c = ' '
            elif thickness == 1:
                inc = -1
                c = '-'
            else:
                inc = -1
                c = '='
        
        for i in range(1,k):
            self.cells[y1+i*dy][x1+i*dx] = c
        
        self.cells[y1][x1] += inc
        self.cells[y2][x2] += inc

    def __str__(self):
        """Return a string representation of the board."""
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
    """The Window; draws a graphical representation of the game onto a
    pygame display."""
    
    TILE_WIDTH = 20
    TILE_HEIGHT = 20
    
    def __init__(self, board):
        """Create a window, displaying the given board.  This will create a
        PyGame Display object (i.e. a window in the GUI)."""
        self.board = board
        
        self.width = self.TILE_WIDTH * board.size
        self.height = self.TILE_HEIGHT * board.size
        
        self.display = pygame.display.set_mode((self.width, self.height))
        
        self.font = pygame.font.SysFont(None, 22)
        
        self.current_tile = None

    def draw_tile(self, row, col):
        """Draw the tile at position (col,row)."""
        x1 = col * self.TILE_WIDTH
        y1 = row * self.TILE_HEIGHT
        w = self.TILE_WIDTH
        h = self.TILE_HEIGHT
        
        # Set background colour depending on whether it's the current tile
        # (i.e. the mouse cursor is over it).
        if self.current_tile == (col, row):
            border_col = (50, 100, 50)
            fill_col = (100, 50, 100)
        else:
            border_col = (50, 50, 100)
            fill_col = (100, 100, 50)
        pygame.draw.rect(self.display, border_col, pygame.Rect(x1, y1, w, h), 1)
        pygame.draw.rect(self.display, fill_col, pygame.Rect(x1+1, y1+1, w-2, h-2))

        if type(self.board.cells[row][col]) is int:
            # Set node colour depending on charge (green positive, red negative).
            if self.board.cells[row][col]  > 0:
                text_col = (0, 255, 0)
            elif self.board.cells[row][col]  < 0:
                text_col = (255, 0, 0)
            else:
                text_col = (255, 255, 255)
            
            # Draw the node value as centered as we can get.
            text = self.font.render("%d" % self.board.cells[row][col], False, text_col)
            tx = x1 + w/2 - text.get_width()/2
            ty = y1 + h/2 - text.get_height()/2
            # + 2 is a fudge factor because digits aren't centered within
            # the font's vertical space.
            self.display.blit(text, (tx, ty + 2))
        
        # Draw a bridge here if necessary.
        elif self.board.cells[row][col] == '|':
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1+w/2, y1, 2, h))
        elif self.board.cells[row][col] == '-':
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1, y1+h/2, w, 2))
        elif self.board.cells[row][col] == 'H':
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1+w/2-2, y1, 2, h))
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1+w/2+2, y1, 2, h))
        elif self.board.cells[row][col] == '=':
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1, y1+h/2-2, w, 2))
            pygame.draw.rect(self.display, (255,255,255), pygame.Rect(x1, y1+h/2+2, w, 2))
    
    def draw(self):
        """Draw the board."""
        
        # First draw all the tiles.
        for i in range(self.board.size):
            for j in range(self.board.size):
                self.draw_tile(i, j)
        
        # Draw an outline for the current possible moves.
        for x1,y1,x2,y2 in self.moves:
            px = x1 * self.TILE_WIDTH
            py = y1 * self.TILE_HEIGHT
            w = (x2 - x1 + 1) * self.TILE_WIDTH
            h = (y2 - y1 + 1) * self.TILE_HEIGHT
            pygame.draw.rect(self.display, (255, 0, 0), pygame.Rect(px, py, w, h), 1)
    
    def update(self):
        """Update the window.  Draw the board, then flip the PyGame display
        to put it on the screen."""
        self.draw()
        pygame.display.flip()


class Control(object):
    """Contoller for the game and window."""
    
    def __init__(self, board, window):
        """Create a controller for the given board and window."""
        self.board = board
        self.window = window
        # This indicates the default direction for building a bridge, as a tie
        # breaker if there is more than one possible bridge orientation where
        # the mouse is clicked.
        self.toggle_dir = False
    
    def update(self):
        """Update the controller.  Return True if the window should be
        redrawn.
        
        Update currently means update the mouse (see update_mouse).
        """
        redraw = False
        if self.update_mouse():
            redraw = True
        
        return redraw

    def update_mouse(self):
        """Update the position of the mouse in the controller.  Return True
        if the window should be redrawn."""
        mx, my = pygame.mouse.get_pos()
        tx = mx/self.window.TILE_WIDTH
        ty = my/self.window.TILE_HEIGHT
        
        # If the mouse is off the board, don't update anything.
        if not self.board.in_range(tx, ty):
            return False
        
        # If the current tile hasn't changed, don't update anything.
        if self.window.current_tile == (tx, ty):
            return False
        
        # Set the current tile and possible moves, and return True so that
        # the window is redrawn with the new information.
        self.window.current_tile = (tx, ty)
        self.window.moves = self.board.find_moves(tx, ty)
        
        return True
    
    def click(self, mx, my):
        """Handle a mouse click in the controller."""
        
        # If no possible moves, don't do anything.
        if self.window.moves == []:
            return
        
        # Otherwise look at current tile's bridge state to see what kind of
        # bridge to build.
        tx, ty = self.window.current_tile
        if self.board.cells[ty][tx] == ' ':
            thickness = 1
        elif self.board.cells[ty][tx] in ['|', '-']:
            thickness = 2
        else:
            thickness = 0
            # If erasing a bridge, alternate the default direction.
            self.toggle_dir = not self.toggle_dir
        
        # Pick the last possible move (horizontal if more than one).
        if self.toggle_dir:
            x1,y1,x2,y2 = self.window.moves[-1]
            if y1 == y2 and self.board.cells[ty][tx] in ['|', 'H']:
                x1,y1,x2,y2 = self.window.moves[0]
        # Or the first possible move (vertical if more than one).
        else:
            x1,y1,x2,y2 = self.window.moves[0]
            if x1 == x2 and self.board.cells[ty][tx] in ['-', '=']:
                x1,y1,x2,y2 = self.window.moves[1]
        
        self.board.draw_line(x1,y1, x2,y2, thickness)
        
        return True


def main(args=None):
    if args is None:
        args = sys.argv
    
    pygame.init()
    
    # Create a board (and unsolve it), a window, and a controller.
    board = Board()
    board.unsolve()
    window = Window(board)
    control = Control(board, window)

    # A user event fires every 500ms to redraw the board, just in case
    # nothing else fires to cause it to be.
    pygame.time.set_timer(pygame.USEREVENT+1, 500)
    
    image_num = 0
    
    while True:
        redraw = False
        ev = pygame.event.wait()
        if ev.type == pygame.KEYDOWN:
            # Press ESC to escape from this ridiculous game!
            if ev.key == pygame.K_ESCAPE:
                break
            # Press r to restart a new game.
            elif ev.key == pygame.K_r:
                board = Board()
                board.unsolve()
                window = Window(board)
                control = Control(board, window)
        # Click to build a bridge on the current spot.
        if ev.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse coordinates and pass to the controller.  Set the
            # redraw flag if we need to redraw.
            mx, my = ev.pos
            redraw = control.click(mx, my)
        elif ev.type == pygame.USEREVENT+1:
            pass
        
        # If the controller indicated we need to redraw, or we got a timer
        # event, then set the redraw flag.
        if control.update() or ev.type == pygame.USEREVENT+1:
            redraw = True
        
        # Redraw if necessary.
        if redraw:
            window.update()
            #print >>sys.stderr, 'update'
            #pygame.image.save(window.display, 'save%04d.png' % image_num)
            image_num += 1

    pygame.quit()


if __name__ == '__main__':
    main()
