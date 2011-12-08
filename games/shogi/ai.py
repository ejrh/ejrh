import game
import random

def get_score(g, x, y):
    return evaluate_game(g)
    
def evaluate_game(g, depth, callback):
    if depth == 0:
        score = evaluate_leaf(g)
        return score, None
    p = g.get_current_player()
    moves = p.get_moves()
    if moves == []:
        return 0, None
    best = None
    if g.current_player == 0:
        i = 0
        for m in moves:
            g2 = g.clone()
            m2 = m.clone(g2)
            p2 = p.clone(g2)
            p2.do_move(m2)
            v, m2 = evaluate_game(g2, depth-1, callback)
            if best is None or v < best_v:
                best = m
                best_v = v
            i += 1
            callback(i, len(moves), depth)
    else:
        i = 0
        for m in moves:
            g2 = g.clone()
            m2 = m.clone(g2)
            p2 = p.clone(g2)
            p2.do_move(m2)
            v, m2 = evaluate_game(g2, depth-1, callback)
            if best is None or v > best_v:
                best = m
                best_v = v
            i += 1
            callback(i, len(moves), depth)
    return best_v, best
    
def evaluate_leaf(g):
    score = 0
    for r in g.board.cells:
        for c in r:
            if c is not None:
                p = piece_value(c)
                if c.player.name == g.players[0].name:
                    p = -p
                score = score + p
    return score
    
def piece_value(p):
    if str(p) == 'K':
        return 999
    if str(p) == 'R':
        return 8
    if str(p) == 'B':
        return 8
    if str(p) == 'G':
        return 7
    if str(p) == 'S':
        return 6
    if str(p) == 'N':
        return 5
    if str(p) == 'L':
        return 3
    if str(p) == 'P':
        return 1
 
try:
    import psyco
    psyco.full()
except ImportError:
    pass

