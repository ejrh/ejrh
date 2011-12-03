import sys
import random



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
                if x2 < 0 or y2 < 0 or x2 >= size or y2 >= size:
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

b = Board()
b.unsolve()
print str(b)
